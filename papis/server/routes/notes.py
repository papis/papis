"""Notes endpoints.

Manage notes attached to documents. All operations also update the document's
``info.yaml``.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import tempfile
from typing import TYPE_CHECKING, Annotated

from fastapi import Body, File, Path, Query, Request, UploadFile
from fastapi.responses import FileResponse

import papis.config
import papis.document
import papis.format
from papis.notes import notes_path_ensured
from papis.paths import make_unique_file, normalize_path_part
from papis.server import exceptions, git as server_git
from papis.server.models import (
    NoteName,
)
from papis.server.routes.documents import (
    _check_folder_exists,
    get_doc,
    get_folder,
)
from papis.server.routes.libraries import get_db, library_router
from papis.server.security import ensure_within_root

if TYPE_CHECKING:
    from papis.document import Document


def _get_note_path(doc: Document, doc_folder: pathlib.Path, id: str) -> pathlib.Path:
    """Return the note file path.

    :raises ResourceNotFoundError: If the document has no notes or the
        file does not exist on disk.
    """
    note = doc.get("notes")
    if not note:
        raise exceptions.ResourceNotFoundError(
            f"Document '{id}' has no notes",
            code=exceptions.ErrorCode.NOTE_NOT_FOUND,
            context={"id": id},
        )

    filepath = doc_folder / str(note)
    if not filepath.exists():
        raise exceptions.ResourceNotFoundError(
            f"Note '{note}' in document '{id}' not found on disk",
            code=exceptions.ErrorCode.NOTE_NOT_FOUND,
            context={"id": id, "note": note},
        )

    return filepath


@library_router.get(
    "/documents/{id}/notes",
    tags=["Document Notes"],
    responses=exceptions.ResourceNotFoundError.responses(
        codes=[
            exceptions.ErrorCode.LIBRARY_NOT_FOUND,
            exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
            exceptions.ErrorCode.NOTE_NOT_FOUND,
        ]
    ),
)
async def download_note(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
) -> FileResponse:
    """Download a document's note."""
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(doc)

    file_path = _get_note_path(doc, doc_folder, id)
    return FileResponse(file_path, filename=file_path.name)


@library_router.post(
    "/documents/{id}/notes",
    status_code=201,
    tags=["Document Notes"],
    responses={
        **exceptions.ResourceNotFoundError.responses(
            codes=[
                exceptions.ErrorCode.LIBRARY_NOT_FOUND,
                exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
                exceptions.ErrorCode.NOTE_NOT_FOUND,
            ]
        ),
        **exceptions.ConflictError.responses(codes=[exceptions.ErrorCode.NOTES_EXIST]),
        **exceptions.PreconditionFailedError.responses(
            codes=[exceptions.ErrorCode.NOT_A_GIT_REPOSITORY]
        ),
    },
)
async def add_note(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    git: Annotated[
        bool | None,
        Query(
            description="Commit changes to git (uses the ``use-git`` option if omitted)"
        ),
    ] = None,
) -> NoteName:
    """Add a note to a document.

    The filename is derived from the ``notes-name`` option, and the content is generated
    from the template set in ``notes-template``. If no template is configured, an empty
    file is created.
    """

    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = _check_folder_exists(doc)
    do_git = server_git.should_use_git(git, doc_folder, root=request.state.lib_path)

    if doc.get("notes"):
        raise exceptions.ConflictError(
            f"Document '{id}' already has notes",
            code=exceptions.ErrorCode.NOTES_EXIST,
            context={"id": id},
        )

    notes_path_ensured(doc)

    db.update(doc)

    if do_git:
        server_git.add_and_commit(
            doc_folder,
            doc["notes"],
            f"Add notes to '{papis.document.describe(doc)}'",
        )
    return NoteName(name=str(doc["notes"]))


@library_router.put(
    "/documents/{id}/notes",
    tags=["Document Notes"],
    responses=exceptions.ResourceNotFoundError.responses(
        codes=[
            exceptions.ErrorCode.LIBRARY_NOT_FOUND,
            exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
            exceptions.ErrorCode.NOTE_NOT_FOUND,
        ]
    )
    | exceptions.PreconditionFailedError.responses(
        codes=[exceptions.ErrorCode.NOT_A_GIT_REPOSITORY]
    ),
)
async def replace_note(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    file_upload: UploadFile = File(description="Note content"),  # ruff:ignore[function-call-in-default-argument]
    git: Annotated[
        bool | None,
        Query(
            description="Commit changes to git (uses the ``use-git`` option if omitted)"
        ),
    ] = None,
) -> NoteName:
    """Replace the content of a document's note."""

    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(doc)
    file_path = _get_note_path(doc, doc_folder, id)
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
            f"Update notes for '{papis.document.describe(doc)}'",
        )

    return NoteName(name=file_path.name)


@library_router.delete(
    "/documents/{id}/notes",
    status_code=204,
    tags=["Document Notes"],
    responses=exceptions.ResourceNotFoundError.responses(
        codes=[
            exceptions.ErrorCode.LIBRARY_NOT_FOUND,
            exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
            exceptions.ErrorCode.NOTE_NOT_FOUND,
        ]
    )
    | exceptions.PreconditionFailedError.responses(
        codes=[exceptions.ErrorCode.NOT_A_GIT_REPOSITORY]
    ),
)
async def delete_note(
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
    """Delete a document's note."""
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(doc)
    do_git = server_git.should_use_git(git, doc_folder, root=request.state.lib_path)

    note = doc.get("notes")
    if not note:
        raise exceptions.ResourceNotFoundError(
            f"Document '{id}' has no notes",
            code=exceptions.ErrorCode.NOTE_NOT_FOUND,
            context={"id": id},
        )

    file_path = doc_folder / note
    file_path.unlink(missing_ok=True)

    del doc["notes"]
    doc.save()
    db.update(doc)

    if do_git:
        server_git.rm_cached(doc_folder, note)
        server_git.add_and_commit(
            doc_folder,
            papis.config.getstring("info-name"),
            f"Remove notes for '{papis.document.describe(doc)}'",
        )


@library_router.patch(
    "/documents/{id}/notes",
    tags=["Document Notes"],
    responses={
        **exceptions.ResourceNotFoundError.responses(
            codes=[
                exceptions.ErrorCode.LIBRARY_NOT_FOUND,
                exceptions.ErrorCode.DOCUMENT_NOT_FOUND,
                exceptions.ErrorCode.NOTE_NOT_FOUND,
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
async def rename_note(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    filename: Annotated[
        str | None,
        Body(
            description="New name or format pattern"
            " (uses the ``notes-name`` option if omitted)",
            embed=True,
        ),
    ] = None,
    git: Annotated[
        bool | None,
        Query(
            description="Commit changes to git (uses the ``use-git`` option if omitted)"
        ),
    ] = None,
) -> NoteName:
    """Rename a document's note."""
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(doc)
    do_git = server_git.should_use_git(git, doc_folder, root=request.state.lib_path)

    note = doc.get("notes")
    if not note:
        raise exceptions.ResourceNotFoundError(
            f"Document '{id}' has no notes",
            code=exceptions.ErrorCode.NOTE_NOT_FOUND,
            context={"id": id},
        )

    file_path_old = doc_folder / note
    if not file_path_old.exists():
        raise exceptions.ResourceNotFoundError(
            f"Note '{note}' in document '{id}' not found on disk",
            code=exceptions.ErrorCode.NOTE_NOT_FOUND,
            context={"id": id, "note": note},
        )

    # Early check. Reject path traversal in the raw filename parameter
    # before it reaches core Papis functions.
    if filename is not None:
        ensure_within_root(doc_folder / filename, doc_folder)

    if filename is not None:
        note_name = papis.format.format(
            filename,
            doc,
            default="",
        )
    else:
        note_name = papis.format.format(
            papis.config.getformatpattern("notes-name"),
            doc,
            default="",
        )

    if not note_name:
        note_name = note

    file_name_new = normalize_path_part(note_name)
    if file_name_new == note:
        return NoteName(name=file_name_new)

    file_path_new = doc_folder / file_name_new
    # Late check. Format patterns could potentially insert arbitrary strings
    file_path_new = ensure_within_root(file_path_new, doc_folder)
    file_path_new = pathlib.Path(make_unique_file(file_path_new))

    file_path_old.rename(file_path_new)

    doc["notes"] = file_path_new.name
    doc.save()
    db.update(doc)

    if do_git:
        server_git.rm_cached(doc_folder, file_path_old.name)
        server_git.add_and_commit(
            doc_folder,
            [file_path_new.name, papis.config.getstring("info-name")],
            f"Rename notes for '{papis.document.describe(doc)}'",
        )

    return NoteName(name=file_path_new.name)
