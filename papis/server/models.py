"""Pydantic models for API request and response bodies."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, create_model

from papis.document import get_document_field_types
from papis.id import ID_KEY_NAME

if TYPE_CHECKING:
    from papis.document import Document


class ErrorDetail(BaseModel):
    """Structured error detail returned by the API."""

    code: str = Field(description="Machine-readable error code.")
    message: str = Field(description="Human-readable explanation of the error.")
    context: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Optional key/value pairs identifying the resource(s) involved (e.g."
            " ``library``, ``id``, ``file``)."
        ),
    )


class ErrorResponse(BaseModel):
    """Top-level error response matching FastAPI's ``{\"detail\": ...}`` convention."""

    detail: ErrorDetail


def _document_field_definitions() -> dict[str, Any]:
    """Field definitions for the document models.

    Each field is optional (``T | None``) and unset by default so that partial
    updates and sparse creations are allowed. Document metadata keys mirror
    the ``info.yaml`` fields.
    """
    key_types = get_document_field_types()
    return {name: (field_type | None, None) for name, field_type in key_types.items()}


if TYPE_CHECKING:

    class PapisRequestDocument(BaseModel):
        model_config = ConfigDict(extra="allow")

    class PapisResponseDocument(BaseModel):
        model_config = ConfigDict(extra="allow")
        papis_id: str

else:
    PapisRequestDocument = create_model(
        "DocumentRequest",
        **_document_field_definitions(),
        __config__=ConfigDict(extra="allow"),
        __doc__=(
            "Document metadata for create/update requests.\n\n"
            "Only the known fields listed below are type-checked. Additional"
            " fields are accepted. All fields are optional."
        ),
    )
    PapisResponseDocument = create_model(
        "DocumentResponse",
        **_document_field_definitions(),
        **{ID_KEY_NAME: (str, ...)},
        __config__=ConfigDict(extra="allow"),
        __doc__=(
            "Document metadata returned by read endpoints.\n\n"
            "Mirrors :class:`DocumentRequest` but requires the ``ID_KEY_NAME`` field"
            " (i.e. ``papis_id``)."
        ),
    )


def document_to_response_model(doc: Document) -> PapisResponseDocument:
    """Convert a papis Document to the API Document model."""

    data = {k: v for k, v in doc.items() if k != ID_KEY_NAME}
    return PapisResponseDocument(**{ID_KEY_NAME: doc[ID_KEY_NAME]}, **data)


class DocumentResponse(BaseModel):
    """A single document with its folder path."""

    document: PapisResponseDocument = Field(description="The document.")
    folder: str | None = Field(
        default=None,
        description="Document folder path relative to the library root.",
    )


class DocumentsResponse(BaseModel):
    """List of documents with their folder paths."""

    documents: list[PapisResponseDocument] = Field(description="List of documents.")
    folders: dict[str, str] = Field(
        description=(
            "Mapping of document ``papis_id`` to folder path relative to the"
            " library root."
        ),
    )


class DocumentRequest(BaseModel):
    """Request body for ``PATCH /documents/{id}``."""

    data: PapisRequestDocument | None = Field(
        default=None,
        description="Key/value pairs to merge into the document metadata.",
    )
    folder: str | None = Field(
        default=None,
        description=(
            "New folder path or format pattern (``null`` for the"
            " ``add-folder-name`` default)."
        ),
    )


class LibraryResponse(BaseModel):
    """Information about a library.

    The library path is only included in local mode.
    """

    name: str = Field(description="Name of the library.")
    path: str | None = Field(default=None, description="Library path.")


class LibrariesResponse(BaseModel):
    """List of libraries."""

    libraries: list[LibraryResponse] = Field(
        description="All libraries known to this server."
    )


class SubfoldersResponse(BaseModel):
    """List of subfolders within a library.

    A sorted list of relative paths (e.g. ``[".", "math", "math/2024", "physics"]``).
    The library root is always included as ``"."``.
    """

    subfolders: list[str] = Field(
        description=("Sorted list of subfolder paths relative to the library root.")
    )


class ExportRequest(BaseModel):
    """Request body for ``POST /export`` — export transient document data."""

    documents: list[PapisRequestDocument] = Field(
        description="List of documents to export."
    )


class FileName(BaseModel):
    """Filename of a file attached to the document."""

    name: str = Field(
        description=(
            "Filename of a file attached to the document, relative to the document's"
            " folder."
        )
    )


class FilesResponse(BaseModel):
    """List of files attached to a document."""

    files: list[FileName] = Field(description="Files attached to the document.")


class NoteName(BaseModel):
    """Filename of the note attached to the document."""

    name: str = Field(
        description=(
            "Filename of the note attached to the document, relative to the document's"
            " folder."
        )
    )


class CitationResponse(BaseModel):
    """A citation or cited-by reference (partial document metadata).

    Fields vary by source: entries from the local library database include
    ``papis_id``, while Crossref-only entries do not. All fields are optional
    and additional unknown fields are allowed.
    """

    model_config = ConfigDict(extra="allow")

    papis_id: str | None = None
    doi: str | None = None
    title: str | None = None
    author: str | None = None
    year: int | None = None
    type: str | None = None
    journal: str | None = None
    ref: str | None = None


class CitationsResponse(BaseModel):
    """List of citations for a document."""

    citations: list[CitationResponse] = Field(description="Citation entries.")


class CitedByResponse(BaseModel):
    """List of documents citing a document."""

    cited_by: list[CitationResponse] = Field(
        description="Documents in the library that cite this document."
    )


class ExporterResponse(BaseModel):
    """Information about an available export format."""

    name: str = Field(
        description="Identifier to pass as ``format`` to the ``POST /export`` endpoint."
    )
    content_type: str = Field(
        description=(
            "MIME type produced by the exporter (e.g. ``application/x-bibtex``)."
        )
    )


class ExportersResponse(BaseModel):
    """List of available export formats."""

    exporters: list[ExporterResponse] = Field(description="Available export formats.")


class ImporterName(BaseModel):
    """Name of a papis importer plugin."""

    name: str = Field(description="Name of a papis importer plugin.")


class ImportersResponse(BaseModel):
    """List of available importers."""

    importers: list[ImporterName] = Field(
        description="Names of all available importer plugins."
    )


class ImporterMatchResponse(BaseModel):
    """Result of matching importers against a URI."""

    matched: list[str] = Field(
        description="Names of importers whose ``match`` step accepted the URI."
    )


class ImporterFetchResponse(BaseModel):
    """Metadata fetched and merged from one or more importers."""

    data: dict[str, Any] = Field(
        description=(
            "Document metadata as key/value pairs, suitable for a ``POST"
            " /documents`` body."
        )
    )


class ConfigResponse(BaseModel):
    """Configuration values for a library, grouped by section.

    Values are the *operative* ones (defaults merged with user config) for the
    requested library. Sensitive keys are filtered out.
    """

    sections: dict[str, dict[str, Any]] = Field(
        description="Mapping of section name to its key/value pairs."
    )


class DoctorError(BaseModel):
    """A single issue found by a doctor check."""

    name: str = Field(description="Name of the check that produced this error.")
    message: str = Field(description="Human-readable description of the problem.")
    payload: str = Field(
        description="String representation of the offending value or document key."
    )
    fix_available: bool = Field(description="Whether this check offers an auto-fixer.")
    fixed: bool = Field(description="Whether the auto-fixer was applied.")


class DoctorResponse(BaseModel):
    """Result of running doctor checks."""

    results: dict[str, list[DoctorError]] = Field(
        description=(
            "Mapping of document ``papis_id`` to the issues found for that document."
        )
    )


class DoctorNameResponse(BaseModel):
    """An available Doctor check."""

    name: str = Field(description="Doctor check name.")


class DoctorChecksResponse(BaseModel):
    """List of available doctor checks."""

    checks: list[DoctorNameResponse] = Field(
        description="Names of all available doctor checks."
    )


class HealthResponse(BaseModel):
    """Server health check response."""

    status: str = Field(description="Server health status.")
