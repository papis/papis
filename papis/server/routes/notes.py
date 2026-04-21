from __future__ import annotations

import pathlib
import shutil
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, File, Path, Query, UploadFile
from fastapi.responses import FileResponse

from papis.paths import _make_unique_file, normalize_path_part
from papis.server import exceptions as api_e
from papis.server.api import API_V1
from papis.server.models import NoteName  # noqa: TC001
from papis.server.routes.documents import get_db, get_doc, get_folder
from papis.server.security import ensure_within_root

if TYPE_CHECKING:
    from papis.document import Document

router = APIRouter(prefix=API_V1)


def _get_note_path(
    doc: Document,
    doc_folder: pathlib.Path,
    note: str,
) -> pathlib.Path:
    """Look up a note in the document's notes list and return its path."""
    notes = doc.get("notes", [])
    if note not in notes:
        raise api_e.ResourceNotFoundError("Note not found in document")

    filepath = doc_folder / note
    if not filepath.exists():
        raise api_e.ResourceNotFoundError("Note not found on disk")

    return filepath


@router.get("/libraries/{library}/documents/{id}/notes", tags=["Notes"])
def list_notes(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
) -> list[NoteName]:
    """List notes in a document."""
    db = get_db(library)
    doc = get_doc(db, id)

    notes = doc.get("notes")
    return [notes] if notes else []


@router.post(
    "/libraries/{library}/documents/{id}/notes",
    status_code=201,
    tags=["Notes"],
    responses={
        **api_e.FilenameRequiredError.responses(),
        **api_e.NotesExistError.responses(),
        **api_e.PathEscapeError.responses(),
    },
)
def add_note(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    upload: UploadFile = File(...),  # noqa: B008
) -> NoteName:
    """Add a note to a document (fails if a notes file already exists)."""
    if not upload.filename:
        # NOTE: this is only reached if function isn't called over HTTP routes
        raise api_e.FilenameRequiredError("Filename is required")

    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(db, id)

    if doc.get("notes"):
        raise api_e.NotesExistError("Document already has notes")

    file_name = normalize_path_part(upload.filename)
    file_path = doc_folder / file_name
    file_path = ensure_within_root(file_path, doc_folder)
    file_path = pathlib.Path(_make_unique_file(file_path))

    with open(file_path, "wb") as dest:
        shutil.copyfileobj(upload.file, dest)

    doc["notes"] = file_path.name
    doc.save()
    db.update(doc)

    return file_path.name


@router.get(
    "/libraries/{library}/documents/{id}/notes/{note}",
    tags=["Notes"],
)
def download_note(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    note: Annotated[str, Path(description="Name of the note")],
) -> FileResponse:
    """Download a note from a document."""
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(db, id)

    file_path = _get_note_path(doc, doc_folder, note)

    return FileResponse(file_path, filename=file_path.name)


@router.put(
    "/libraries/{library}/documents/{id}/notes/{note}",
    tags=["Notes"],
)
def replace_note(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    note: Annotated[str, Path(description="Name of the note")],
    upload: UploadFile = File(...),  # noqa: B008
) -> NoteName:
    """Replace a note in a document."""
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(db, id)
    file_path = _get_note_path(doc, doc_folder, note)

    with open(file_path, "wb") as dest:
        shutil.copyfileobj(upload.file, dest)

    return file_path.name


@router.delete(
    "/libraries/{library}/documents/{id}/notes/{note}",
    status_code=204,
    tags=["Notes"],
)
def delete_note(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    note: Annotated[str, Path(description="Name of the note")],
) -> None:
    """Delete a note from a document."""
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(db, id)

    file_path = _get_note_path(doc, doc_folder, note)

    file_path.unlink()

    del doc["notes"]
    doc.save()
    db.update(doc)


@router.patch(
    "/libraries/{library}/documents/{id}/notes",
    tags=["Notes"],
    responses=api_e.PathEscapeError.responses(),
)
def rename_note(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    old_note: str = Query(..., description="Current name of the note"),
    new_note: str = Query(..., description="New name for the note"),
) -> NoteName:
    """Rename a note in a document."""
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(db, id)
    file_path_old = _get_note_path(doc, doc_folder, old_note)

    file_name_new = normalize_path_part(new_note)
    file_path_new = doc_folder / file_name_new
    file_path_new = ensure_within_root(file_path_new, doc_folder)
    file_path_new = pathlib.Path(_make_unique_file(file_path_new))

    file_path_old.rename(file_path_new)

    doc["notes"] = file_path_new.name
    doc.save()
    db.update(doc)

    return file_path_new.name
