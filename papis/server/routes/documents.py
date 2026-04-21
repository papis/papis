from __future__ import annotations

import pathlib
import shutil
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import APIRouter, Path, Query, Response

import papis.database
from papis.document import Document
from papis.paths import _make_unique_folder, normalize_path_part
from papis.server import exceptions as api_e
from papis.server.api import API_V1
from papis.server.models import (
    DocFolder,
    DocumentInput,
    DocumentResponse,
    document_to_output_model,
)
from papis.server.routes.exporters import (
    DOCUMENT_RESPONSES,
    export_documents,
    validate_format,
)
from papis.server.routes.libraries import get_library_info
from papis.server.security import ensure_within_root

if TYPE_CHECKING:
    from papis.database.base import Database

router = APIRouter(prefix=API_V1)


def get_db(library: str) -> Database:
    """Get database for a library name."""
    _, _ = get_library_info(library)
    return papis.database.get(library)


def get_doc(db: Database, id: str) -> Document:
    """Get a document by ID, raising 404 if not found."""
    doc = db.find_by_id(id)
    if not doc:
        raise api_e.ResourceNotFoundError("Document not found")
    return doc


def get_folder(db: Database, id: str) -> pathlib.Path:
    """Get a document's folder by ID, raising 404 if not found or folder missing."""
    doc = get_doc(db, id)
    folder = doc.get_main_folder()
    if not folder or not pathlib.Path(folder).exists():
        raise api_e.ResourceNotFoundError("Document folder not found")
    return pathlib.Path(folder)


def _normalize_doc_path(path: str) -> pathlib.Path:
    """Splits the path into components, normalizes each one, then rejoins."""
    parts = pathlib.Path(path).parts
    normalized = [normalize_path_part(c) for c in parts if c and c != "."]
    return pathlib.Path(*normalized) if normalized else Path()


def _reject_files_notes(data: dict[str, Any]) -> None:
    """Reject requests that include files or notes in document data."""
    if "files" in data or "notes" in data:
        raise api_e.FilesNotAllowedError(
            "Files and notes must be managed via their dedicated endpoints"
        )


@router.get(
    "/libraries/{library}/documents",
    tags=["Documents"],
    response_model=list[DocumentResponse],
    response_model_exclude_none=True,
    responses={**DOCUMENT_RESPONSES, **api_e.UnknownExportFormat.responses()},
)
def get_documents(
    library: Annotated[str, Path(description="Library name")],
    q: str | None = Query(None, description="Query string to filter documents"),
    format: str = Query(default="json", description="Export format"),
) -> list[DocumentResponse] | Response:
    """Get documents from a library, optionally filtered by query."""
    db = get_db(library)

    if q:
        docs = db.query(q)
    else:
        docs = db.get_all_documents()

    validate_format(format)

    if format != "json":
        content, content_type = export_documents(docs, format)
        headers = (
            {"Content-Disposition": f'attachment; filename="documents.{format}"'}
            if format != "json"
            else {}
        )
        return Response(content=content, media_type=content_type, headers=headers)

    return [document_to_output_model(doc) for doc in docs]


@router.get(
    "/libraries/{library}/documents/{id}",
    tags=["Documents"],
    response_model=DocumentResponse,
    response_model_exclude_none=True,
    responses={**DOCUMENT_RESPONSES, **api_e.UnknownExportFormat.responses()},
)
def get_document(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    format: str = Query(default="json", description="Export format"),
) -> DocumentResponse | Response:
    """Get a specific document by ID."""
    db = get_db(library)
    doc = get_doc(db, id)

    validate_format(format)

    if format != "json":
        content, content_type = export_documents([doc], format)
        filename = f"{doc.get_main_folder_name()}.{format}"
        headers = (
            {"Content-Disposition": f'attachment; filename="{filename}"'}
            if format != "json"
            else {}
        )
        return Response(content=content, media_type=content_type, headers=headers)

    return document_to_output_model(doc)


@router.post(
    "/libraries/{library}/documents",
    status_code=201,
    response_model_exclude_none=True,
    tags=["Documents"],
    responses={
        **api_e.PathEscapeError.responses(),
        **api_e.FilesNotAllowedError.responses(),
    },
)
def create_document(
    data: DocumentInput,
    library: Annotated[str, Path(description="Library name")],
    folder: str = Query(
        ..., description="The document folder's path within the library"
    ),
) -> DocumentResponse:
    """Create a new document in a library.

    Note that files and notes must be managed via the dedicated endpoints.
    """
    _, lib_path = get_library_info(library)
    db = get_db(library)

    doc_data = {k: v for k, v in data.model_dump().items() if v is not None}
    _reject_files_notes(doc_data)

    doc_path_norm = lib_path / _normalize_doc_path(folder)
    doc_path = ensure_within_root(doc_path_norm, lib_path)
    doc_path = pathlib.Path(_make_unique_folder(doc_path))
    doc_path.mkdir(parents=True, exist_ok=True)
    doc = Document(folder=str(doc_path), data=doc_data)
    db.maybe_compute_id(doc)
    doc.save()

    db.add(doc)

    return document_to_output_model(doc)


@router.patch(
    "/libraries/{library}/documents/{id}",
    response_model_exclude_none=True,
    tags=["Documents"],
    responses=api_e.FilesNotAllowedError.responses(),
)
def update_document(
    data: DocumentInput,
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
) -> DocumentResponse:
    """Update a document's metadata.

    Note that files and notes must be managed via the dedicated endpoints.
    """
    db = get_db(library)
    doc = get_doc(db, id)

    update_data = data.model_dump(exclude_unset=True)
    _reject_files_notes(update_data)

    doc.update(update_data)
    # NOTE: remove this once https://github.com/papis/papis/issues/1164 is resolved
    for key in list(doc):
        value = doc[key]
        if (
            value is None
            or (isinstance(value, str) and not value)
            or (isinstance(value, (list, dict)) and not value)
        ):
            del doc[key]

    doc.save()

    db.update(doc)

    return document_to_output_model(doc)


@router.delete(
    "/libraries/{library}/documents/{id}",
    status_code=204,
    tags=["Documents"],
)
def delete_document(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
) -> None:
    """Delete a document."""
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(db, id)

    if doc_folder.exists():
        shutil.rmtree(doc_folder)

    db.delete(doc)


@router.get(
    "/libraries/{library}/documents/{id}/folder",
    tags=["Document folder"],
)
def get_document_folder(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
) -> DocFolder:
    """Get the path of a document relative to the library root."""
    _, lib_path = get_library_info(library)
    db = get_db(library)
    doc_folder = get_folder(db, id)

    return str(doc_folder.relative_to(lib_path))


@router.patch(
    "/libraries/{library}/documents/{id}/folder",
    tags=["Document folder"],
    responses=api_e.PathEscapeError.responses(),
)
def move_document(
    library: Annotated[str, Path(description="Library name")],
    id: Annotated[str, Path(description="Document ID")],
    folder: str = Query(
        ..., description="The document folder's path within the library"
    ),
) -> DocFolder:
    """Move a document to a new location within the library."""
    _, lib_path = get_library_info(library)
    db = get_db(library)
    doc = get_doc(db, id)
    doc_folder = get_folder(db, id)

    doc_path_norm = lib_path / _normalize_doc_path(folder)
    doc_path_new = ensure_within_root(doc_path_norm, lib_path)
    doc_path_new = pathlib.Path(_make_unique_folder(doc_path_new))
    shutil.move(doc_folder, doc_path_new)

    doc.set_folder(str(doc_path_new))

    db.delete(doc)
    db.add(doc)

    return str(doc_path_new.relative_to(lib_path))
