"""Exporter listing and advisory export.

Provides the ``GET /exporters`` listing endpoint and the ``POST /export`` endpoint
for exporting arbitrary document data (both stored and transient).
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import Body, Path, Query, Response

import papis.config
from papis.document import from_data
from papis.exporters import get_available_exporters, get_exporter_by_name
from papis.server import exceptions
from papis.server.models import ExporterResponse, ExportersResponse, ExportRequest
from papis.server.routes.libraries import library_router

_EXPORT_CONTENT_TYPES: dict[str, str] = {
    "json": "application/json",
    "bibtex": "text/x-bibtex",
    "yaml": "application/yaml",
    "csl": "text/plain",
    "typst": "application/yaml",
    "csv": "text/csv",
}
_DEFAULT_CONTENT_TYPE = "text/plain"

_AVAILABLE_FORMATS: set[str] = set(get_available_exporters()) | {"json"}


def _validate_format(name: str) -> None:
    """Validate that the format name is a known exporter.

    :raises BadRequestError: If the format is not in the available exporters.
    """
    if name not in _AVAILABLE_FORMATS:
        valid = ", ".join(sorted(_AVAILABLE_FORMATS))
        raise exceptions.BadRequestError(
            f"Unknown export format '{name}'. Available formats: {valid}",
            code=exceptions.ErrorCode.UNKNOWN_EXPORT_FORMAT,
            context={"format": name},
        )


@library_router.get(
    "/export",
    response_model=ExportersResponse,
    tags=["Export"],
    responses=exceptions.ResourceNotFoundError.responses(
        codes=[
            exceptions.ErrorCode.LIBRARY_NOT_FOUND,
        ]
    ),
)
async def list_exporters(
    library: Annotated[str, Path(description="Library name")],
) -> ExportersResponse:
    """List all available export formats."""
    return ExportersResponse(
        exporters=[
            ExporterResponse(
                name=name,
                content_type=_EXPORT_CONTENT_TYPES.get(name, _DEFAULT_CONTENT_TYPE),
            )
            for name in sorted(_AVAILABLE_FORMATS)
        ]
    )


@library_router.post(
    "/export",
    tags=["Export"],
    responses={
        **exceptions.ResourceNotFoundError.responses(
            codes=[exceptions.ErrorCode.LIBRARY_NOT_FOUND]
        ),
        **exceptions.BadRequestError.responses(
            codes=[exceptions.ErrorCode.UNKNOWN_EXPORT_FORMAT]
        ),
    },
)
async def export_documents(
    library: Annotated[str, Path(description="Library name")],
    body: Annotated[ExportRequest, Body(description="Documents to export")],
    format: Annotated[
        str,
        Query(description="Export format, e.g. 'bibtex', 'yaml', 'json'"),
    ],
) -> Response:
    """Export document data to a named format.

    In local mode, ``_papis_local_folder`` is injected into each document that has a
    ``papis_id`` matching a document in the library.
    """
    _validate_format(format)
    docs: list[dict[str, Any]] = [
        d.model_dump(exclude_unset=True) for d in body.documents
    ]

    if papis.config.getboolean("server-local-mode"):
        from papis.server.routes.libraries import get_db

        db = get_db(library)
        for doc in docs:
            papis_id = doc.get("papis_id")
            if papis_id:
                stored_doc = db.find_by_id(papis_id)
                if stored_doc:
                    folder = stored_doc.get_main_folder()
                    if folder:
                        doc["_papis_local_folder"] = folder

    documents = [from_data(d) for d in docs]
    content_type = _EXPORT_CONTENT_TYPES.get(format, _DEFAULT_CONTENT_TYPE)
    exporter = get_exporter_by_name(format)
    content = exporter(documents)

    return Response(content=content, media_type=content_type)
