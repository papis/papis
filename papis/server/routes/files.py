from __future__ import annotations

import pathlib
import shutil
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, File, Path, Query, UploadFile
from fastapi.responses import FileResponse

from papis.paths import _make_unique_file, normalize_path_part
from papis.server import exceptions as api_e
from papis.server.api import API_V1
from papis.server.models import FileName  # noqa: TC001
from papis.server.routes.documents import get_db, get_doc, get_folder
from papis.server.security import ensure_within_root

if TYPE_CHECKING:
    from papis.document import Document

router = APIRouter(prefix=API_V1)


def _get_file_path(
    doc: Document,
    doc_folder: pathlib.Path,
    file: str,
) -> pathlib.Path:
    """Look up a file in the document's files list and return its path."""
    files: list[str] = doc.get("files", [])
    if file not in files:
        raise api_e.ResourceNotFoundError("File not found in document")

    filepath = doc_folder / file
    if not filepath.exists():
        raise api_e.ResourceNotFoundError("File not found on disk")

    return filepath


@router.get("/libraries/{library}/documents/{id}/files", tags=["Files"])
def list_files(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
) -> list[FileName]:
    """List files in a document."""
    db = get_db(library)
    doc = get_doc(db, id)

    return doc.get("files") or []


@router.post(
    "/libraries/{library}/documents/{id}/files",
    status_code=201,
    tags=["Files"],
    responses={
        **api_e.FilenameRequiredError.responses(),
        **api_e.PathEscapeError.responses(),
    },
)
def add_file(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    upload: UploadFile = File(...),  # noqa: B008
) -> FileName:
    """Add a file to a document."""
    if not upload.filename:
        # NOTE: this is only reached if function isn't called over HTTP routes
        raise api_e.FilenameRequiredError("Filename is required")

    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(db, id)

    file_name = normalize_path_part(upload.filename)
    file_path = doc_folder / file_name
    file_path = ensure_within_root(file_path, doc_folder)
    file_path = pathlib.Path(_make_unique_file(file_path))

    with open(file_path, "wb") as dest:
        shutil.copyfileobj(upload.file, dest)

    doc.setdefault("files", [])
    doc["files"].append(file_path.name)
    doc.save()
    db.update(doc)

    return file_path.name


@router.get(
    "/libraries/{library}/documents/{id}/files/{file}",
    tags=["Files"],
)
def download_file(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    file: Annotated[str, Path(description="Name of the file")],
) -> FileResponse:
    """Download a file from a document."""
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(db, id)

    file_path = _get_file_path(doc, doc_folder, file)

    return FileResponse(file_path, filename=file_path.name)


@router.put(
    "/libraries/{library}/documents/{id}/files/{file}",
    tags=["Files"],
)
def replace_file(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    file: Annotated[str, Path(description="Name of the file")],
    upload: UploadFile = File(...),  # noqa: B008
) -> FileName:
    """Replace a file in a document."""
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(db, id)
    file_path = _get_file_path(doc, doc_folder, file)

    with open(file_path, "wb") as dest:
        shutil.copyfileobj(upload.file, dest)

    return file_path.name


@router.delete(
    "/libraries/{library}/documents/{id}/files/{file}",
    status_code=204,
    tags=["Files"],
)
def delete_file(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    file: Annotated[str, Path(description="Name of the file")],
) -> None:
    """Delete a file from a document."""
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(db, id)

    file_path = _get_file_path(doc, doc_folder, file)

    file_path.unlink()

    doc["files"].remove(file)
    doc.save()
    db.update(doc)


@router.patch(
    "/libraries/{library}/documents/{id}/files",
    tags=["Files"],
    responses=api_e.PathEscapeError.responses(),
)
def rename_file(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    old_file: str = Query(..., description="Current name of the file"),
    new_file: str = Query(..., description="New name for the file"),
) -> FileName:
    """Rename a file in a document."""
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(db, id)

    file_path_old = _get_file_path(doc, doc_folder, old_file)

    file_name_new = normalize_path_part(new_file)
    file_path_new = doc_folder / file_name_new
    file_path_new = ensure_within_root(file_path_new, doc_folder)
    file_path_new = pathlib.Path(_make_unique_file(file_path_new))

    file_path_old.rename(file_path_new)

    doc["files"].remove(old_file)
    doc["files"].append(file_path_new.name)
    doc.save()
    db.update(doc)

    return file_path_new.name
