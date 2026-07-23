"""Files endpoints.

Manage files attached to documents. All operations also update the document's
``info.yaml``.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import tempfile
from typing import TYPE_CHECKING, Annotated

from fastapi import Body, File, Form, Path, Query, Request, UploadFile
from fastapi.responses import FileResponse

import papis.config
import papis.document
from papis.paths import (
    get_document_file_name,
    make_unique_file,
    normalize_path_part,
)
from papis.server import exceptions, git as server_git
from papis.server.models import (
    FileName,
    FilesResponse,
)
from papis.server.routes.documents import get_doc, get_folder, resolve_and_symlink
from papis.server.routes.libraries import get_db, library_router
from papis.server.security import ensure_within_root

if TYPE_CHECKING:
    from papis.document import Document


def _check_file_in_metadata(
    id: str,
    doc: Document,
    file: str,
) -> None:
    """Check if *file* is in the document's files metadata.

    :raises ResourceNotFoundError: If the file is not listed in ``doc["files"]``.
    """
    files: list[str] = doc.get("files", [])
    if file not in files:
        raise exceptions.ResourceNotFoundError(
            f"File '{file}' not found in document '{id}'",
            code=exceptions.ErrorCode.FILE_NOT_FOUND,
            context={"id": id, "file": file},
        )


def _get_file_path(
    id: str,
    doc: Document,
    doc_folder: pathlib.Path,
    file: str,
) -> pathlib.Path:
    """Look up a file in the document's files list and return its path.

    :raises ResourceNotFoundError: If the file is not listed in metadata
        or does not exist on disk.
    """
    _check_file_in_metadata(id, doc, file)

    filepath = doc_folder / file
    if not filepath.exists():
        raise exceptions.ResourceNotFoundError(
            f"File '{file}' in document '{id}' not found on disk",
            code=exceptions.ErrorCode.FILE_NOT_FOUND,
            context={"id": id, "file": file},
        )

    return filepath


@library_router.get(
    "/documents/{id}/files",
    tags=["Document Files"],
    response_model=FilesResponse,
    responses=exceptions.ResourceNotFoundError.responses(
        codes=[
            exceptions.ErrorCode.LIBRARY_NOT_FOUND,
            exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
            exceptions.ErrorCode.FILE_NOT_FOUND,
        ]
    ),
)
async def list_files(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
) -> FilesResponse:
    """List files in a document."""
    db = get_db(library)
    doc = get_doc(db, id)

    return FilesResponse(files=[FileName(name=f) for f in doc.get("files", [])])


@library_router.post(
    "/documents/{id}/files",
    status_code=201,
    tags=["Document Files"],
    responses={
        **exceptions.ResourceNotFoundError.responses(
            codes=[
                exceptions.ErrorCode.LIBRARY_NOT_FOUND,
                exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
                exceptions.ErrorCode.FILE_NOT_FOUND,
            ]
        ),
        **exceptions.BadRequestError.responses(
            codes=[
                exceptions.ErrorCode.PATH_ESCAPE,
                exceptions.ErrorCode.MUTUALLY_EXCLUSIVE,
                exceptions.ErrorCode.LOCAL_MODE_REQUIRED,
            ]
        ),
        **exceptions.PreconditionFailedError.responses(
            codes=[exceptions.ErrorCode.NOT_A_GIT_REPOSITORY]
        ),
    },
)
async def add_file(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    file_upload: Annotated[UploadFile | None, File(description="File to add")] = None,
    link_file: Annotated[
        str | None,
        Form(description="Source path to symlink into the document (local mode only)"),
    ] = None,
    filename: Annotated[
        str | None,
        Form(
            description="File name format pattern"
            " (uses the ``add-file-name`` option if omitted)"
        ),
    ] = None,
    git: Annotated[
        bool | None,
        Query(
            description="Commit changes to git (uses the ``use-git`` option if omitted)"
        ),
    ] = None,
) -> FileName:
    """Add a file to a document.

    Provide either ``file_upload`` (to copy the uploaded file) or ``link_file``
    (to symlink a local path). ``link_file`` requires ``server-local-mode``).
    """

    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(doc)
    do_git = server_git.should_use_git(git, doc_folder, root=request.state.lib_path)

    if file_upload is not None and link_file is not None:
        raise exceptions.BadRequestError(
            "Provide either 'file_upload' or 'link_file', not both.",
            code=exceptions.ErrorCode.MUTUALLY_EXCLUSIVE,
        )

    if file_upload is not None:
        # can only happen when the function isn't called via HTTP
        assert file_upload.filename is not None

        tmp_dir = tempfile.mkdtemp()

        # Sanitize the uploaded filename so ``open()`` succeeds on all platforms.
        tmp_name = normalize_path_part(pathlib.Path(file_upload.filename).name)
        tmp_path = pathlib.Path(tmp_dir) / tmp_name
        with open(tmp_path, "wb") as dest:
            shutil.copyfileobj(file_upload.file, dest)

        try:
            # Early check. Reject path traversal in the raw file_name parameter
            # before it reaches core Papis functions.
            if filename is not None:
                ensure_within_root(doc_folder / filename, doc_folder)

            filename = get_document_file_name(
                doc, str(tmp_path), file_name_format=filename
            )

            file_path = doc_folder / filename
            # Late check. Format patterns could potentially insert arbitrary strings
            file_path = ensure_within_root(file_path, doc_folder)
            file_path = pathlib.Path(make_unique_file(file_path))

            shutil.move(str(tmp_path), str(file_path))
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    elif link_file is not None:
        if not papis.config.getboolean("server-local-mode"):
            raise exceptions.BadRequestError(
                "``link_files`` requires the server to run in local mode.",
                code=exceptions.ErrorCode.LOCAL_MODE_REQUIRED,
            )

        file_path = resolve_and_symlink(
            doc, doc_folder, link_file, file_name_format=filename
        )

    doc.setdefault("files", []).append(file_path.name)
    doc.save()
    db.update(doc)

    if do_git:
        server_git.add_and_commit(
            doc_folder,
            [file_path.name, papis.config.getstring("info-name")],
            f"Add file '{file_path.name}' to '{papis.document.describe(doc)}'",
        )

    return FileName(name=file_path.name)


@library_router.get(
    "/documents/{id}/files/{file}",
    tags=["Document Files"],
    responses=exceptions.ResourceNotFoundError.responses(
        codes=[
            exceptions.ErrorCode.LIBRARY_NOT_FOUND,
            exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
            exceptions.ErrorCode.FILE_NOT_FOUND,
        ]
    ),
)
async def download_file(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    file: Annotated[str, Path(description="Name of the file")],
) -> FileResponse:
    """Download a file from a document."""
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(doc)

    file_path = _get_file_path(id, doc, doc_folder, file)

    return FileResponse(file_path, filename=file_path.name)


@library_router.put(
    "/documents/{id}/files/{file}",
    tags=["Document Files"],
    responses=exceptions.ResourceNotFoundError.responses(
        codes=[
            exceptions.ErrorCode.LIBRARY_NOT_FOUND,
            exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
            exceptions.ErrorCode.FILE_NOT_FOUND,
        ]
    )
    | exceptions.PreconditionFailedError.responses(
        codes=[exceptions.ErrorCode.NOT_A_GIT_REPOSITORY]
    ),
)
async def replace_file(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    file: Annotated[str, Path(description="Name of the file")],
    file_upload: UploadFile = File(description="File with replacement content"),  # ruff:ignore[function-call-in-default-argument]
    git: Annotated[
        bool | None,
        Query(
            description="Commit changes to git (uses the ``use-git`` option if omitted)"
        ),
    ] = None,
) -> FileName:
    """Replace a file in a document."""

    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(doc)
    file_path = _get_file_path(id, doc, doc_folder, file)
    do_git = server_git.should_use_git(git, doc_folder, root=request.state.lib_path)

    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(doc_folder), prefix=".tmp-")
    try:
        with open(tmp_fd, "wb") as dest:
            shutil.copyfileobj(file_upload.file, dest)
        os.replace(tmp_path, str(file_path))
    except BaseException:
        pathlib.Path(tmp_path).unlink(missing_ok=True)
        raise

    if do_git:
        server_git.add_and_commit(
            doc_folder,
            file_path.name,
            f"Update file '{file_path.name}' for '{papis.document.describe(doc)}'",
        )

    return FileName(name=file_path.name)


@library_router.delete(
    "/documents/{id}/files/{file}",
    status_code=204,
    tags=["Document Files"],
    responses=exceptions.ResourceNotFoundError.responses(
        codes=[
            exceptions.ErrorCode.LIBRARY_NOT_FOUND,
            exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
            exceptions.ErrorCode.FILE_NOT_FOUND,
        ]
    )
    | exceptions.PreconditionFailedError.responses(
        codes=[exceptions.ErrorCode.NOT_A_GIT_REPOSITORY]
    ),
)
async def delete_file(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    file: Annotated[str, Path(description="Name of the file")],
    git: Annotated[
        bool | None,
        Query(
            description="Commit changes to git (uses the ``use-git`` option if omitted)"
        ),
    ] = None,
) -> None:
    """Delete a file from a document."""
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(doc)
    do_git = server_git.should_use_git(git, doc_folder, root=request.state.lib_path)

    _check_file_in_metadata(id, doc, file)

    file_path = doc_folder / file
    file_path.unlink(missing_ok=True)

    doc["files"].remove(file)
    doc.save()
    db.update(doc)

    if do_git:
        server_git.rm_cached(doc_folder, file_path.name)
        server_git.add_and_commit(
            doc_folder, papis.config.getstring("info-name"), f"Remove file '{file}'"
        )


@library_router.patch(
    "/documents/{id}/files/{file}",
    tags=["Document Files"],
    responses={
        **exceptions.ResourceNotFoundError.responses(
            codes=[
                exceptions.ErrorCode.LIBRARY_NOT_FOUND,
                exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
                exceptions.ErrorCode.FILE_NOT_FOUND,
            ]
        ),
        **exceptions.BadRequestError.responses(
            codes=[exceptions.ErrorCode.PATH_ESCAPE]
        ),
        **exceptions.PreconditionFailedError.responses(
            codes=[exceptions.ErrorCode.NOT_A_GIT_REPOSITORY]
        ),
    },
)
async def rename_file(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    file: Annotated[str, Path(description="Current name of the file")],
    filename: Annotated[
        str | None,
        Body(
            description="New name or format pattern"
            " (uses the ``add-file-name`` option if omitted)",
            embed=True,
        ),
    ] = None,
    git: Annotated[
        bool | None,
        Query(
            description="Commit changes to git (uses the ``use-git`` option if omitted)"
        ),
    ] = None,
) -> FileName:
    """Rename a file in a document."""
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(doc)
    do_git = server_git.should_use_git(git, doc_folder, root=request.state.lib_path)

    file_path_old = _get_file_path(id, doc, doc_folder, file)

    # Early check. Reject path traversal in the raw filename parameter
    # before it reaches core Papis functions.
    if filename is not None:
        ensure_within_root(doc_folder / filename, doc_folder)

    file_name_new = get_document_file_name(
        doc, str(file_path_old), file_name_format=filename
    )
    if file_name_new == file:
        return FileName(name=file_name_new)

    file_path_new = doc_folder / file_name_new
    # Late check. Format patterns could potentially insert arbitrary strings
    file_path_new = ensure_within_root(file_path_new, doc_folder)
    file_path_new = pathlib.Path(make_unique_file(file_path_new))

    file_path_old.rename(file_path_new)

    doc["files"].remove(file)
    doc["files"].append(file_path_new.name)
    doc.save()
    db.update(doc)

    if do_git:
        server_git.rm_cached(doc_folder, file_path_old.name)
        server_git.add_and_commit(
            doc_folder,
            [file_path_new.name, papis.config.getstring("info-name")],
            f"Rename file '{file}' to '{file_path_new.name}'",
        )

    return FileName(name=file_path_new.name)
