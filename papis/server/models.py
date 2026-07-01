from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, create_model

from papis.document import get_document_field_types
from papis.id import ID_KEY_NAME

if TYPE_CHECKING:
    from papis.document import Document


DocFolder = Annotated[
    str, Field(description="Path of the document folder relative to the library root")
]
FileName = Annotated[str, Field(description="Name of the file in the document folder")]
NoteName = Annotated[str, Field(description="Name of the note in the document folder")]
ImporterName = Annotated[str, Field(description="Name of an importer")]


def _document_field_definitions() -> dict[str, Any]:
    """Return field definitions for document models."""
    key_types = get_document_field_types()
    return {name: (field_type | None, None) for name, field_type in key_types.items()}


if TYPE_CHECKING:

    class DocumentInput(BaseModel):
        model_config = ConfigDict(extra="allow")

    class DocumentResponse(BaseModel):
        model_config = ConfigDict(extra="allow")
        papis_id: str

else:
    DocumentInput = create_model(
        "DocumentInput",
        **_document_field_definitions(),
        __config__=ConfigDict(extra="allow"),
    )
    DocumentResponse = create_model(
        "DocumentResponse",
        **_document_field_definitions(),
        **{ID_KEY_NAME: (str, ...)},
        __config__=ConfigDict(extra="allow"),
    )


class LibraryResponse(BaseModel):
    """Information about a library."""

    name: str
    # path: str  # NOTE: for security reasons, we don't return this


class ExporterResponse(BaseModel):
    """Information about an available export format."""

    name: str
    content_type: str


class ImporterMatchInput(BaseModel):
    """Input for matching importers against a URI."""

    uri: str


class ImporterMatchResponse(BaseModel):
    """Result of matching importers against a URI."""

    matched: list[str]


class ImporterFetchResponse(BaseModel):
    """Result of fetching metadata from an importer."""

    importer: str
    data: dict[str, Any]


def document_to_output_model(doc: Document) -> DocumentResponse:
    """Convert a papis Document to the API Document model."""

    data = {k: v for k, v in doc.items() if k != ID_KEY_NAME}
    papis_id = doc.get(ID_KEY_NAME, "")

    return DocumentResponse(**{ID_KEY_NAME: papis_id}, **data)
