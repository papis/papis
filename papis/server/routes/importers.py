from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path

from papis.importer import (
    fetch_importers,
    get_available_importers,
    get_importer_by_name,
    get_matching_importers_by_uri,
)
from papis.server import exceptions as api_e
from papis.server.api import API_V1
from papis.server.models import (
    ImporterFetchResponse,
    ImporterMatchInput,
    ImporterMatchResponse,
    ImporterName,
)

# NOTE: Only match importers in the papis.importer namespace.
# Downloaders are reached through the 'url' importer (WebImporter), which
# dispatches to the best matching downloader internally.
_INCLUDE_DOWNLOADERS = False


router = APIRouter(prefix=API_V1)


@router.get("/importers", tags=["Importers"])
def list_importers() -> list[ImporterName]:
    """List all available importer names."""
    return get_available_importers()


@router.post(
    "/importers/match", response_model=ImporterMatchResponse, tags=["Importers"]
)
def match_importers(input: ImporterMatchInput) -> ImporterMatchResponse:
    """Match importers capable of handling a given URI."""
    importers = get_matching_importers_by_uri(
        input.uri, include_downloaders=_INCLUDE_DOWNLOADERS
    )
    return ImporterMatchResponse(matched=[imp.name for imp in importers])


@router.post(
    "/importers/{importer}/fetch",
    response_model=ImporterFetchResponse,
    tags=["Importers"],
    responses={
        **api_e.InvalidURIError.responses(),
        **api_e.UpstreamError.responses(),
    },
)
def fetch_metadata(
    importer: Annotated[str, Path(description="Importer name")],
    input: ImporterMatchInput,
) -> ImporterFetchResponse:
    """Fetch metadata using a specific importer."""
    try:
        cls = get_importer_by_name(importer)
    except Exception as e:
        raise api_e.ResourceNotFoundError(f"Importer '{importer}' not found") from e

    matched_importer = cls.match(input.uri)
    if matched_importer is None:
        raise api_e.InvalidURIError(
            f"Importer '{importer}' cannot handle the given URI"
        )

    imported_metadata = fetch_importers([matched_importer], download_files=False)
    if not imported_metadata:
        raise api_e.UpstreamError("Failed to fetch data from upstream source")

    if not imported_metadata[0].ctx.data:
        raise api_e.ImporterNoDataError("Importer returned no data")

    return ImporterFetchResponse(
        importer=importer,
        data=imported_metadata[0].ctx.data,
    )
