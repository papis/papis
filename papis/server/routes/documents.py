"""Document and folder management endpoints.

Files and notes are managed via separate endpoints.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import tempfile
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import File, Form, Header, Path, Query, Request, Response, UploadFile

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
    doc_metadata_to_response_model,
)
from papis.server.routes.libraries import get_db, library_router
from papis.server.security import ensure_within_root

if TYPE_CHECKING:
    from papis.database.base import Database
    from papis.document import Document
    from papis.server.events import EventBroker


def get_doc(db: Database, id: str) -> Document:
    """Get a document by ID.

    :raises ResourceNotFoundError: If the document does not exist.
    """
    doc = db.find_by_id(id)
    if not doc:
        raise exceptions.ResourceNotFoundError(
            f"Document '{id}' not found",
            type=exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
            context={"id": id},
        )
    return doc


def _find_nesting_parent(
    folder: pathlib.Path,
    lib_path: pathlib.Path,
    db: Database,
) -> pathlib.Path | None:
    """Return the first ancestor of *folder* that is a document folder.

    :param folder: The folder to check.
    :param lib_path: The library root path (ancestors above this are ignored).
    :param db: The library database.
    :return: The offending ancestor path, or ``None``.
    """
    return next(
        (
            ancestor
            for ancestor in folder.parents
            if ancestor != lib_path
            and lib_path in ancestor.parents
            and db.find_by_folder(str(ancestor)) is not None
        ),
        None,
    )


def _check_folder_exists(doc: Document) -> pathlib.Path:
    """Return the document folder.

    :raises ResourceNotFoundError: If the folder does not exist on disk.
    """
    folder = doc.get_main_folder()
    if not folder or not pathlib.Path(folder).exists():
        raise exceptions.ResourceNotFoundError(
            f"Folder not found for document '{doc.get('papis_id', 'unknown')}'."
            " The database may be stale. Try clearing the cache for this library.",
            type=exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
        )
    return pathlib.Path(folder)


def get_folder(doc: Document) -> pathlib.Path:
    """Get a document's folder.

    :raises ResourceNotFoundError: If the folder does not exist on disk.
    """
    return _check_folder_exists(doc)


_IMMUTABLE_FIELDS = frozenset(["files", "notes", "papis_id"])


def _reject_immutable_field_changes(
    metadata: dict[str, Any], doc: Document | None = None
) -> None:
    """Reject attempts to change immutable metadata fields.

    :param metadata: Fields the client wants to set.
    :param doc: The existing document, or ``None`` if no existing document.
    :raises BadRequestError: If the client tries to change an immutable field.
    """
    for field in _IMMUTABLE_FIELDS:
        if field in metadata:
            current_val = doc.get(field) if doc is not None else None
            new_val = metadata[field]
            if new_val != current_val:
                if field in {"files", "notes"}:
                    message = (
                        f"The '{field}' field cannot be changed through document"
                        f" metadata. Use the dedicated /{field} endpoint."
                    )
                else:
                    message = f"The '{field}' field is immutable."
                raise exceptions.BadRequestError(
                    message,
                    type=exceptions.ErrorCode.IMMUTABLE_FIELD,
                    context={"field": field},
                )


def _check_if_match(
    library: str, id: str, if_match: str | None, request: Request
) -> None:
    """Check If-Match precondition header.

    :param library: Library name.
    :param id: Document papis_id.
    :param if_match: The ``If-Match`` header value (or ``None``).
    :param request: The FastAPI request object.
    :raises PreconditionFailedError: If the document version isn't the expected version.
    """
    if if_match is not None:
        current_version = request.app.state.broker.get_doc_version(library, id)
        expected_version = int(if_match.strip('"'))
        if current_version != expected_version:
            raise exceptions.PreconditionFailedError(
                f"Document '{id}' has been modified since version {expected_version}",
                type=exceptions.ErrorCode.VERSION_MISMATCH,
                context={
                    "id": id,
                    "expected_version": expected_version,
                    "current_version": current_version,
                },
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
            type=exceptions.ErrorCode.FILE_NOT_FOUND,
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
    responses={
        **exceptions.ResourceNotFoundError.responses(
            types=[
                exceptions.ErrorCode.LIBRARY_NOT_FOUND,
            ]
        ),
        **exceptions.BadRequestError.responses(
            types=[
                exceptions.ErrorCode.MUTUALLY_EXCLUSIVE,
            ]
        ),
    },
)
async def get_documents(
    request: Request,
    response: Response,
    library: Annotated[str, Path(description="Library name")],
    q: str | None = Query(
        None,
        description="Query string to filter documents.",
    ),
    folder: str | None = Query(
        None,
        description="Folder path prefix relative to the library root. Returns documents"
        " whose folder equals or is a subfolder of the given path.",
    ),
    id: Annotated[
        list[str] | None,
        Query(
            description="Papis IDs to match. May be provided multiple times.",
        ),
    ] = None,
    since_version: int | None = Query(
        None,
        description="Return only documents with version > this value",
    ),
    sort: str | None = Query(
        None,
        description="Sort field name. Uses the ``sort-field`` option when no ``q`` is"
        " given. With ``q``, the default is to sort documents by relevance.",
    ),
    reverse: bool | None = Query(
        None,
        description="Reverse the sort order. Uses the ``sort-reverse`` option if"
        " omitted.",
    ),
    limit: int | None = Query(
        None,
        ge=0,
        description="Maximum number of documents to return. Capped by the"
        "``server-max-page-size`` option.",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Zero-based offset into the matching documents.",
    ),
    if_none_match: str | None = Header(None, alias="If-None-Match"),
) -> DocumentsResponse | Response:
    """Get documents and their folders, optionally filtered by query.

    ``q``, ``folder``, and ``id`` can be combined. All filters must match (AND
    semantics). ``since_version`` is mutually exclusive with ``q``,
    ``folder``, and ``id``.
    """
    db = get_db(library)
    broker: EventBroker = request.app.state.broker

    if if_none_match is not None:
        current_version = broker.get_lib_version(library)
        if current_version == int(if_none_match.strip('"')):
            return Response(status_code=304)

    if q == "":
        q = None
    if folder == "":
        folder = None
    ids = None
    if id is not None:
        ids = [value for value in id if value] or None

    if since_version is not None and (
        q is not None or folder is not None or id is not None
    ):
        raise exceptions.BadRequestError(
            "'since_version' is mutually exclusive with 'q', 'folder', and 'id'",
            type=exceptions.ErrorCode.MUTUALLY_EXCLUSIVE,
        )

    if q is None:
        q = db.get_all_query_string()

    effective_limit = limit
    if limit is not None:
        max_page_size = papis.config.getint("server-max-page-size")
        if max_page_size:
            effective_limit = min(limit, max_page_size)

    if since_version is not None:
        changed_ids = broker.get_document_ids_since(library, since_version)
        docs = [d for d in (db.find_by_id(id) for id in changed_ids) if d is not None]
        total = len(docs)
        effective_limit = None
    else:
        docs, total = db.query_paged(
            q,
            folder=folder,
            ids=ids,
            sort=sort,
            reverse=reverse,
            limit=effective_limit,
            offset=offset,
        )

    lib_path = request.state.lib_path
    documents = [
        DocumentResponse(
            metadata=doc_metadata_to_response_model(doc),
            folder=_relative_folder(doc, lib_path),
        )
        for doc in docs
    ]

    response.headers["ETag"] = f'"{broker.get_lib_version(library)}"'

    return DocumentsResponse(
        total=total,
        limit=effective_limit,
        offset=offset if since_version is None else 0,
        documents=documents,
    )


@library_router.post(
    "/documents",
    status_code=201,
    response_model=DocumentResponse,
    tags=["Documents"],
    responses={
        **exceptions.ResourceNotFoundError.responses(
            types=[
                exceptions.ErrorCode.LIBRARY_NOT_FOUND,
            ]
        ),
        **exceptions.BadRequestError.responses(
            types=[
                exceptions.ErrorCode.INVALID_JSON,
                exceptions.ErrorCode.LOCAL_MODE_REQUIRED,
                exceptions.ErrorCode.PATH_ESCAPE,
                exceptions.ErrorCode.IMMUTABLE_FIELD,
            ]
        ),
        **exceptions.PreconditionFailedError.responses(
            types=[exceptions.ErrorCode.NOT_A_GIT_REPOSITORY]
        ),
    },
)
async def add_document(
    request: Request,
    response: Response,
    library: Annotated[str, Path(description="Library name")],
    metadata: Annotated[str, Form(description="JSON document metadata")],
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
    filename: Annotated[
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

    Suffixes are added as needed to resolve folder and file name collisions.
    """

    try:
        doc_data = json.loads(metadata)
    except json.JSONDecodeError as exc:
        raise exceptions.BadRequestError(
            "Invalid JSON in 'metadata' field",
            type=exceptions.ErrorCode.INVALID_JSON,
            context={"error": str(exc)},
        ) from exc
    if link_files and not papis.config.getboolean("server-local-mode"):
        raise exceptions.BadRequestError(
            "``link_files`` requires the server to run in local mode.",
            type=exceptions.ErrorCode.LOCAL_MODE_REQUIRED,
        )
    _reject_immutable_field_changes(doc_data)

    staging_paths = _stage_uploaded_files(files)

    db = get_db(library)
    lib_path = request.state.lib_path
    broker: EventBroker = request.app.state.broker
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
            file_name_format=filename,
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
                    doc, doc_temp_dir, src, file_name_format=filename
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

        response.headers["ETag"] = (
            f'"{broker.get_doc_version(library, doc.get("papis_id", ""))}"'
        )

        return DocumentResponse(
            metadata=doc_metadata_to_response_model(doc),
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
    responses={
        **exceptions.ResourceNotFoundError.responses(
            types=[
                exceptions.ErrorCode.LIBRARY_NOT_FOUND,
                exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
            ]
        ),
    },
)
async def get_document(
    request: Request,
    response: Response,
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    if_none_match: str | None = Header(None, alias="If-None-Match"),
) -> DocumentResponse | Response:
    """Get a document and its folder.

    Supports conditional requests via the ``If-None-Match`` header. Standard responses
    include an ``ETag`` based on the document's version. If the client sends a request
    with a ``If-None-Match`` matching the document's version, a ``304 Not Modified``
    response is returned instead of the document.
    """
    db = get_db(library)
    doc = get_doc(db, id)
    broker: EventBroker = request.app.state.broker

    if if_none_match is not None:
        current_version = broker.get_doc_version(library, id)
        if current_version == int(if_none_match.strip('"')):
            return Response(status_code=304)

    response.headers["ETag"] = f'"{broker.get_doc_version(library, id)}"'

    return DocumentResponse(
        metadata=doc_metadata_to_response_model(doc),
        folder=_relative_folder(doc, request.state.lib_path),
    )


@library_router.patch(
    "/documents/{id}",
    response_model=DocumentResponse,
    tags=["Documents"],
    responses={
        **exceptions.ResourceNotFoundError.responses(
            types=[
                exceptions.ErrorCode.LIBRARY_NOT_FOUND,
                exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
            ]
        ),
        **exceptions.BadRequestError.responses(
            types=[
                exceptions.ErrorCode.IMMUTABLE_FIELD,
                exceptions.ErrorCode.PATH_ESCAPE,
            ]
        ),
        **exceptions.ConflictError.responses(
            types=[
                exceptions.ErrorCode.FOLDER_EXISTS,
                exceptions.ErrorCode.FOLDER_INSIDE_DOCUMENT,
            ]
        ),
        **exceptions.PreconditionFailedError.responses(
            types=[
                exceptions.ErrorCode.NOT_A_GIT_REPOSITORY,
                exceptions.ErrorCode.VERSION_MISMATCH,
            ]
        ),
    },
)
async def update_or_move_document(
    request: Request,
    response: Response,
    body: DocumentRequest,
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    if_match: str | None = Header(None, alias="If-Match"),
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

    Format patterns are resolved, but no suffixes are added to folder names to avoid
    collisions. Collisions with existing folders raise an error. The only exception to
    this rule obtains when trying to move a document's folder to _it's own_ folder --
    this is a no-op.

    Use the ``If-Match`` header to avoid updating documents that have been changed by a
    third party. Set it to the document's version (from the ``ETag`` of a previous
    ``GET``) to ensure no other client has modified the document in the meantime. If the
    version doesn't match, a ``412 Precondition Failed`` response is returned.
    """
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = _check_folder_exists(doc)
    lib_path = request.state.lib_path
    broker: EventBroker = request.app.state.broker
    _check_if_match(library, id, if_match, request)

    do_git = server_git.should_use_git(git, doc_folder, root=lib_path)
    if body.metadata is not None:
        update_data = body.metadata.model_dump(exclude_unset=True)
        _reject_immutable_field_changes(update_data, doc)

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
            papis.paths.get_document_folder(
                doc, lib_path, folder_name_format=body.folder
            )
        )

        # Late check. Format patterns could potentially insert arbitrary strings
        new_folder = ensure_within_root(new_folder, lib_path)

        if new_folder.resolve() == old_folder.resolve():
            pass  # Document folder unchanged
        elif (
            nesting_parent := _find_nesting_parent(new_folder, lib_path, db)
        ) is not None:
            raise exceptions.ConflictError(
                f"Target folder '{new_folder}' would nest inside an existing document's"
                f" folder: '{nesting_parent}'",
                type=exceptions.ErrorCode.FOLDER_INSIDE_DOCUMENT,
                context={
                    "new_folder": new_folder.relative_to(lib_path).as_posix(),
                    "existing_folder": nesting_parent.relative_to(lib_path).as_posix(),
                },
            )
        elif new_folder.exists():
            raise exceptions.ConflictError(
                f"Target folder already exists: '{new_folder}'",
                type=exceptions.ErrorCode.FOLDER_EXISTS,
                context={"folder": new_folder.relative_to(lib_path).as_posix()},
            )
        else:
            papis.document.move(doc, str(new_folder))

            if do_git:
                server_git.rm_cached(lib_path, str(old_folder), recursive=True)
                server_git.add_and_commit(
                    lib_path,
                    str(new_folder.relative_to(lib_path)),
                    f"Move '{papis.document.describe(doc)}'",
                )

            db.update(doc)

    response.headers["ETag"] = f'"{broker.get_doc_version(library, id)}"'

    return DocumentResponse(
        metadata=doc_metadata_to_response_model(doc),
        folder=_relative_folder(doc, lib_path),
    )


@library_router.delete(
    "/documents/{id}",
    status_code=204,
    tags=["Documents"],
    responses=exceptions.ResourceNotFoundError.responses(
        types=[
            exceptions.ErrorCode.LIBRARY_NOT_FOUND,
            exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
        ]
    )
    | exceptions.PreconditionFailedError.responses(
        types=[
            exceptions.ErrorCode.NOT_A_GIT_REPOSITORY,
            exceptions.ErrorCode.VERSION_MISMATCH,
        ]
    ),
)
async def delete_document(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    if_match: str | None = Header(None, alias="If-Match"),
    git: Annotated[
        bool | None,
        Query(
            description="Commit changes to git (uses the ``use-git`` option if omitted)"
        ),
    ] = None,
) -> None:
    """Delete a document.

    Use the ``If-Match`` header to avoid deleting documents that have been changed by a
    third party. Set it to the document's version (from the ``ETag`` of a previous
    ``GET``) to ensure no other client has modified the document in the meantime. If the
    version doesn't match, a ``412 Precondition Failed`` response is returned.
    """
    lib_path = request.state.lib_path
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(doc)
    _check_if_match(library, id, if_match, request)

    do_git = server_git.should_use_git(git, lib_path, root=lib_path)

    shutil.rmtree(doc_folder)

    if do_git:
        server_git.rm_cached(lib_path, str(doc_folder), recursive=True)
        server_git.commit(
            lib_path,
            f"Remove document '{papis.document.describe(doc)}'",
        )
    db.delete(doc)
