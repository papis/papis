"""Document and folder management endpoints.

Files and notes are managed via separate endpoints.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import tempfile
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import File, Form, Path, Query, Request, Response, UploadFile

import papis.config
import papis.doctor
import papis.document
import papis.hooks
import papis.paths
import papis.strings
from papis.server import exceptions, git as server_git
from papis.server.models import (
    DocumentRequest,
    DocumentResponse,
    DocumentsResponse,
    document_to_response_model,
)
from papis.server.routes.libraries import get_db, library_router
from papis.server.security import ensure_within_root

if TYPE_CHECKING:
    from papis.database.base import Database
    from papis.document import Document


def get_doc(db: Database, id: str) -> Document:
    """Get a document by ID.

    :raises ResourceNotFoundError: If the document does not exist.
    """
    doc = db.find_by_id(id)
    if not doc:
        raise exceptions.ResourceNotFoundError(
            f"Document '{id}' not found",
            code=exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
            context={"id": id},
        )
    return doc


def _check_folder_exists(doc: Document) -> pathlib.Path:
    """Return the document folder.

    :raises ResourceNotFoundError: If the folder does not exist on disk.
    """
    folder = doc.get_main_folder()
    if not folder or not pathlib.Path(folder).exists():
        raise exceptions.ResourceNotFoundError(
            f"Folder not found for document '{doc.get('papis_id', 'unknown')}'."
            " The database may be stale. Try clearing the cache for this library.",
            code=exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
        )
    return pathlib.Path(folder)


def get_folder(doc: Document) -> pathlib.Path:
    """Get a document's folder.

    :raises ResourceNotFoundError: If the folder does not exist on disk.
    """
    return _check_folder_exists(doc)


_READ_ONLY_FIELDS = frozenset(["files", "notes", "papis_id"])


def _reject_read_only_fields(data: dict[str, Any]) -> None:
    """Reject requests that try to modify read-only metadata fields.

    :raises BadRequestError: If any field from ``_READ_ONLY_FIELDS`` is present.
    """
    for field in _READ_ONLY_FIELDS:
        if field in data:
            if field in {"files", "notes"}:
                message = (
                    "The 'files' and 'notes' fields cannot be set through document"
                    " metadata. Use the dedicated /files and /notes endpoints (or the"
                    " 'files' form field when creating a new document)."
                )
            else:
                message = f"The '{field}' field is read-only and cannot be modified."
            raise exceptions.BadRequestError(
                message,
                code=exceptions.ErrorCode.READ_ONLY_FIELD,
                context={"field": field},
            )


def _stage_uploaded_files(files: list[UploadFile]) -> list[pathlib.Path]:
    """Save uploaded files to temporary paths.

    :param files: Uploaded files.
    :return: A list of temporary file paths.
    """
    staging: list[pathlib.Path] = []
    for f in files:
        tmp = tempfile.NamedTemporaryFile(delete=False)
        shutil.copyfileobj(f.file, tmp)
        tmp.close()
        staging.append(pathlib.Path(tmp.name))
    return staging


def _cleanup_staging_files(paths: list[pathlib.Path]) -> None:
    """Remove temporary staging files, ignoring any errors."""
    for p in paths:
        p.unlink(missing_ok=True)


def _relative_folder(doc: Document, lib_path: pathlib.Path) -> str:
    """Return the document's folder path relative to the library root.

    :returns: Forward-slash-separated relative path.
    :raises ResourceNotFoundError: If the folder does not exist on disk.
    """
    doc_folder = _check_folder_exists(doc)
    return doc_folder.relative_to(lib_path).as_posix()


def resolve_and_symlink(
    doc: Document,
    doc_folder: pathlib.Path,
    source: str,
    *,
    file_name_format: str | None = None,
) -> pathlib.Path:
    """Resolve filename and create a symlink in *doc_folder*.

    :param doc: The document.
    :param doc_folder: The document's folder on disk.
    :param source: Absolute path to symlink.
    :param file_name_format: File name format pattern.
    :returns: The filename.
    :raises ResourceNotFoundError: If the source file does not exist.
    """
    src_path = pathlib.Path(source)
    if not src_path.exists():
        raise exceptions.ResourceNotFoundError(
            f"Source file for symlink does not exist: '{source}'",
            code=exceptions.ErrorCode.FILE_NOT_FOUND,
            context={"source": source},
        )

    file_name = papis.paths.get_document_file_name(
        doc, str(src_path), file_name_format=file_name_format
    )
    file_path = doc_folder / file_name
    file_path = pathlib.Path(papis.paths.make_unique_file(file_path))

    papis.paths.symlink(str(src_path), str(file_path))
    return file_path


@library_router.get(
    "/documents",
    tags=["Documents"],
    response_model=DocumentsResponse,
    response_model_exclude_none=True,
    responses={
        **exceptions.ResourceNotFoundError.responses(
            codes=[
                exceptions.ErrorCode.LIBRARY_NOT_FOUND,
            ]
        ),
        **exceptions.BadRequestError.responses(
            codes=[
                exceptions.ErrorCode.MUTUALLY_EXCLUSIVE,
            ]
        ),
    },
)
async def get_documents(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
    q: str | None = Query(None, description="Query string to filter documents"),
) -> DocumentsResponse:
    """Get documents and their folders, optionally filtered by query.

    ``q`` and ``since_version`` are mutually exclusive.
    """
    db = get_db(library)

    if q:
        docs = db.query(q)
    else:
        docs = db.get_all_documents()

    lib_path = request.state.lib_path
    doc_models = [document_to_response_model(doc) for doc in docs]
    folders: dict[str, str] = {}
    for doc in docs:
        folder_rel = _relative_folder(doc, lib_path)
        folders[doc["papis_id"]] = folder_rel

    return DocumentsResponse(documents=doc_models, folders=folders)


@library_router.post(
    "/documents",
    status_code=201,
    response_model=DocumentResponse,
    response_model_exclude_none=True,
    tags=["Documents"],
    responses={
        **exceptions.BadRequestError.responses(
            codes=[
                exceptions.ErrorCode.INVALID_JSON,
                exceptions.ErrorCode.LOCAL_MODE_REQUIRED,
                exceptions.ErrorCode.PATH_ESCAPE,
                exceptions.ErrorCode.READ_ONLY_FIELD,
            ]
        ),
        **exceptions.PreconditionFailedError.responses(
            codes=[exceptions.ErrorCode.NOT_A_GIT_REPOSITORY]
        ),
    },
)
async def add_document(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
    data: Annotated[str, Form(description="JSON document metadata")],
    files: Annotated[
        list[UploadFile],
        File(description="Files to attach to the document"),
    ] = [],  # ruff:ignore[mutable-argument-default]
    link_files: Annotated[
        list[str],
        Form(description="Source paths to symlink into the document (local mode only)"),
    ] = [],  # ruff:ignore[mutable-argument-default]
    folder: Annotated[
        str | None,
        Form(
            description="Folder path within library"
            " (uses the ``add-folder-name`` option if omitted)"
        ),
    ] = None,
    file_name: Annotated[
        str | None,
        Form(
            description="File name format pattern"
            " (uses the ``add-file-name`` option if omitted)"
        ),
    ] = None,
    auto_doctor: Annotated[
        bool | None,
        Query(
            description="Run doctor auto-fixers on the new document"
            " (uses the ``auto-doctor`` option if omitted)"
        ),
    ] = None,
    git: Annotated[
        bool | None,
        Query(
            description="Commit changes to git (uses the ``use-git`` option if omitted)"
        ),
    ] = None,
) -> DocumentResponse:
    """Create a new document.

    Pass ``link_files`` (list of absolute source paths) to symlink instead of copying.
    This requires ``server-local-mode``.
    """

    try:
        doc_data = json.loads(data)
    except json.JSONDecodeError as exc:
        raise exceptions.BadRequestError(
            "Invalid JSON in 'data' field",
            code=exceptions.ErrorCode.INVALID_JSON,
            context={"error": str(exc)},
        ) from exc
    if link_files and not papis.config.getboolean("server-local-mode"):
        raise exceptions.BadRequestError(
            "``link_files`` requires the server to run in local mode.",
            code=exceptions.ErrorCode.LOCAL_MODE_REQUIRED,
        )
    _reject_read_only_fields(doc_data)

    staging_paths = _stage_uploaded_files(files)

    db = get_db(library)
    lib_path = request.state.lib_path
    do_git = server_git.should_use_git(git, lib_path, root=lib_path)

    if papis.config.getboolean("time-stamp"):
        doc_data["time-added"] = papis.strings.get_timestamp()

    doc_temp_dir = None
    try:
        doc = papis.document.new(
            data=doc_data,
            files=[str(p) for p in staging_paths],
            auto_doctor=(
                auto_doctor
                if auto_doctor is not None
                else papis.config.getboolean("auto-doctor") or False
            ),
            file_name_format=file_name,
        )
        # Early check. Reject path traversal in the raw folder parameter before it
        # reaches core Papis functions.
        if folder is not None:
            ensure_within_root(lib_path / folder, lib_path)

        doc_temp_dir = _check_folder_exists(doc)
        doc_folder = pathlib.Path(
            papis.paths.get_document_unique_folder(
                doc, lib_path, folder_name_format=folder
            )
        )
        # Late check. Format patterns could potentially insert arbitrary strings
        doc_folder = ensure_within_root(doc_folder, lib_path)

        if link_files:
            for src in link_files:
                file_path = resolve_and_symlink(
                    doc, doc_temp_dir, src, file_name_format=file_name
                )
                doc.setdefault("files", []).append(file_path.name)
            doc.save()

        papis.hooks.run("on_add_done", doc)

        papis.document.move(doc, str(doc_folder))
        db.add(doc)

        if do_git:
            resources = [papis.config.getstring("info-name"), *doc.get("files", [])]
            server_git.add_and_commit(
                doc_folder,
                resources,
                f"Add document '{papis.document.describe(doc)}'",
            )

        return DocumentResponse(
            document=document_to_response_model(doc),
            folder=_relative_folder(doc, lib_path),
        )
    finally:
        _cleanup_staging_files(staging_paths)
        if doc_temp_dir:
            shutil.rmtree(doc_temp_dir, ignore_errors=True)


@library_router.get(
    "/documents/{id}",
    tags=["Documents"],
    response_model=DocumentResponse,
    response_model_exclude_none=True,
    responses={
        **exceptions.ResourceNotFoundError.responses(
            codes=[
                exceptions.ErrorCode.LIBRARY_NOT_FOUND,
                exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
            ]
        ),
    },
)
async def get_document(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
) -> DocumentResponse | Response:
    """Get a document and its folder.

    Supports conditional requests via the ``If-None-Match`` header. Standard responses
    include an ``ETag`` based on the document's version. If the client sends a request
    with a ``If-None-Match`` matching the document's version, a ``304 Not Modified``
    response is returned instead of the document.
    """
    db = get_db(library)
    doc = get_doc(db, id)

    return DocumentResponse(
        document=document_to_response_model(doc),
        folder=_relative_folder(doc, request.state.lib_path),
    )


@library_router.patch(
    "/documents/{id}",
    response_model=DocumentResponse,
    response_model_exclude_none=True,
    tags=["Documents"],
    responses={
        **exceptions.ResourceNotFoundError.responses(
            codes=[
                exceptions.ErrorCode.LIBRARY_NOT_FOUND,
                exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
            ]
        ),
        **exceptions.BadRequestError.responses(
            codes=[
                exceptions.ErrorCode.READ_ONLY_FIELD,
                exceptions.ErrorCode.PATH_ESCAPE,
            ]
        ),
        **exceptions.PreconditionFailedError.responses(
            codes=[exceptions.ErrorCode.NOT_A_GIT_REPOSITORY]
        ),
    },
)
async def update_document(
    request: Request,
    body: DocumentRequest,
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    auto_doctor: Annotated[
        bool | None,
        Query(
            description="Run doctor auto-fixers after updating"
            " (uses the ``auto-doctor`` option if omitted)"
        ),
    ] = None,
    git: Annotated[
        bool | None,
        Query(
            description="Commit changes to git (uses the ``use-git`` option if omitted)"
        ),
    ] = None,
) -> DocumentResponse:
    """Update a document's metadata, move it, or both.

    Either ``data``, ``folder``, or both may be present. When both are
    present the metadata update happens first so that format patterns in the
    folder name can reference the new values.

    Files and notes must be managed via the dedicated endpoints.
    """
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = _check_folder_exists(doc)
    lib_path = request.state.lib_path

    do_git = server_git.should_use_git(git, doc_folder, root=lib_path)
    if body.data is not None:
        update_data = body.data.model_dump(exclude_unset=True)
        _reject_read_only_fields(update_data)

        doc.update(update_data)

        if (
            auto_doctor
            if auto_doctor is not None
            else papis.config.getboolean("auto-doctor") or False
        ):
            papis.doctor.fix_errors(doc)

        doc.save()
        db.update(doc)

        if do_git:
            server_git.add_and_commit(
                doc_folder,
                papis.config.getstring("info-name"),
                f"Update information for '{papis.document.describe(doc)}'",
            )

    if "folder" in body.model_dump(exclude_unset=True):
        old_folder = get_folder(doc)

        # Early check. Reject path traversal in the raw folder parameter before it
        # reaches core Papis functions.
        if body.folder is not None:
            ensure_within_root(lib_path / body.folder, lib_path)

        new_folder = pathlib.Path(
            papis.paths.get_document_unique_folder(
                doc, lib_path, folder_name_format=body.folder
            )
        )

        # Late check. Format patterns could potentially insert arbitrary strings
        new_folder = ensure_within_root(new_folder, lib_path)
        papis.document.move(doc, str(new_folder))

        if do_git:
            server_git.rm_cached(lib_path, str(old_folder), recursive=True)
            server_git.add_and_commit(
                lib_path,
                str(new_folder.relative_to(lib_path)),
                f"Move '{papis.document.describe(doc)}'",
            )

        db.update(doc)

    return DocumentResponse(
        document=document_to_response_model(doc),
        folder=_relative_folder(doc, lib_path),
    )


@library_router.delete(
    "/documents/{id}",
    status_code=204,
    tags=["Documents"],
    responses=exceptions.ResourceNotFoundError.responses(
        codes=[
            exceptions.ErrorCode.LIBRARY_NOT_FOUND,
            exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
        ]
    )
    | exceptions.PreconditionFailedError.responses(
        codes=[exceptions.ErrorCode.NOT_A_GIT_REPOSITORY]
    ),
)
async def delete_document(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    git: Annotated[
        bool | None,
        Query(
            description="Commit changes to git (uses the ``use-git`` option if omitted)"
        ),
    ] = None,
) -> None:
    """Delete a document."""
    lib_path = request.state.lib_path
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(doc)

    do_git = server_git.should_use_git(git, lib_path, root=lib_path)

    shutil.rmtree(doc_folder)

    if do_git:
        server_git.rm_cached(lib_path, str(doc_folder), recursive=True)
        server_git.commit(
            lib_path,
            f"Remove document '{papis.document.describe(doc)}'",
        )
    db.delete(doc)
