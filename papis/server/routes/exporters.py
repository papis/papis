from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter

from papis.exporters import get_available_exporters, get_exporter_by_name
from papis.server import exceptions as api_e
from papis.server.models import ExporterResponse

if TYPE_CHECKING:
    from papis.document import Document

from papis.server.api import API_V1

router = APIRouter(prefix=API_V1)

_EXPORT_CONTENT_TYPES: dict[str, str] = {
    # Special default case
    "json": "application/json",
    # Other formats
    "bibtex": "text/x-bibtex",
    "yaml": "application/yaml",
    "csl": "application/vnd.citationstyles.style+xml",
    "typst": "text/vnd.typst",
    "csv": "text/csv",
}

_AVAILABLE_FORMATS: set[str] = set(get_available_exporters()) | {"json"}

# OpenAPI "responses" dict to document the non-json format options
DOCUMENT_RESPONSES: dict[str | int, dict[str, Any]] = {
    200: {
        "description": "Documents in the requested format",
        "content": {
            _EXPORT_CONTENT_TYPES[name]: {"schema": {"type": "string"}}
            for name in _EXPORT_CONTENT_TYPES
            if name in _AVAILABLE_FORMATS and name != "json"
        },
    }
}


def export_documents(docs: list[Document], name: str) -> tuple[str, str]:
    """Export documents to the given format."""
    content_type = _EXPORT_CONTENT_TYPES.get(name, "text/plain")
    exporter = get_exporter_by_name(name)
    content = exporter(docs)
    return content, content_type


def validate_format(name: str) -> None:
    """Raise 400 if the format name is not a known exporter."""
    if name not in _AVAILABLE_FORMATS:
        valid = ", ".join(sorted(_AVAILABLE_FORMATS))
        raise api_e.UnknownExportFormat(
            f"Unknown export format: '{name}'. Available formats: {valid}"
        )


@router.get("/exporters", tags=["Exporters"])
def list_exporters() -> list[ExporterResponse]:
    """List all available export formats.

    To export documents to specific formats, use the document endpoints.
    """
    return [
        ExporterResponse(name=name, content_type=content_type)
        for name, content_type in _EXPORT_CONTENT_TYPES.items()
        if name in _AVAILABLE_FORMATS
    ]
