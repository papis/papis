"""Importer endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import Body, Path, Query

from papis.importer import (
    collect_from_importers,
    fetch_importers,
    get_available_importers,
    get_matching_importers_by_name,
    get_matching_importers_by_uri,
)
from papis.server import exceptions
from papis.server.models import (
    ImporterFetchResponse,
    ImporterMatchResponse,
    ImporterName,
    ImportersResponse,
)
from papis.server.routes.libraries import library_router

# NOTE: Only match importers in the papis.importer namespace.
# Downloaders are reached through the 'url' importer (WebImporter), which
# dispatches to the best matching downloader internally.
_INCLUDE_DOWNLOADERS = False

# Importers that require local filesystem access and aren't handled by the server.
_FILESYSTEM_IMPORTERS = frozenset({"folder", "lib"})


@library_router.get("/import", tags=["Import"], response_model=ImportersResponse)
async def list_importers(
    library: Annotated[str, Path(description="Library name")],
) -> ImportersResponse:
    """List all available importer names."""
    return ImportersResponse(
        importers=[
            ImporterName(name=name)
            for name in get_available_importers()
            if name not in _FILESYSTEM_IMPORTERS
        ]
    )


@library_router.post(
    "/import/match", response_model=ImporterMatchResponse, tags=["Import"]
)
async def match_importers(
    library: Annotated[str, Path(description="Library name")],
    uri: Annotated[
        str,
        Body(
            description="A URI or identifier such as a DOI, arXiv ID, or URL.",
            embed=True,
        ),
    ],
) -> ImporterMatchResponse:
    """Match importers capable of handling a given URI."""
    importers = get_matching_importers_by_uri(
        uri, include_downloaders=_INCLUDE_DOWNLOADERS
    )
    return ImporterMatchResponse(matched=[imp.name for imp in importers])


@library_router.post(
    "/import/fetch",
    response_model=ImporterFetchResponse,
    tags=["Import"],
    responses={
        **exceptions.ResourceNotFoundError.responses(
            codes=[exceptions.ErrorCode.IMPORTER_NOT_FOUND]
        ),
        **exceptions.BadRequestError.responses(
            codes=[
                exceptions.ErrorCode.INVALID_URI,
                exceptions.ErrorCode.LOCAL_MODE_REQUIRED,
            ]
        ),
        **exceptions.UpstreamError.responses(
            codes=[exceptions.ErrorCode.UPSTREAM_ERROR]
        ),
    },
)
async def fetch_from_importers(
    library: Annotated[str, Path(description="Library name")],
    uri: Annotated[
        str,
        Body(
            description="A URI or identifier such as a DOI, arXiv ID, or URL.",
            embed=True,
        ),
    ],
    importers: Annotated[
        list[str] | None,
        Query(
            description=("Importers to use. Omit to match all available importers."),
        ),
    ] = None,
) -> ImporterFetchResponse:
    """Fetch and merge metadata from one or more importers.

    Unknown importers raise a 404. Importers that don't match the URI are
    silently skipped.
    """
    if importers is not None:
        available = set(get_available_importers())
        requested = set(importers)
        missing = requested - available
        if missing:
            raise exceptions.ResourceNotFoundError(
                f"Importer(s) not found: {', '.join(missing)}",
                code=exceptions.ErrorCode.IMPORTER_NOT_FOUND,
                context={"importers": sorted(missing)},
            )

        blocked = requested & _FILESYSTEM_IMPORTERS
        if blocked:
            raise exceptions.BadRequestError(
                "Importers that require local filesystem access"
                f" cannot be used remotely: {', '.join(sorted(blocked))}",
                code=exceptions.ErrorCode.LOCAL_MODE_REQUIRED,
                context={"importers": sorted(blocked)},
            )

        name_and_uris = [(name, uri) for name in importers]
        matched = get_matching_importers_by_name(name_and_uris)
    else:
        matched = get_matching_importers_by_uri(
            uri, include_downloaders=_INCLUDE_DOWNLOADERS
        )

    if not matched:
        attempted = importers or []
        raise exceptions.BadRequestError(
            f"Importers cannot handle URI '{uri}': {', '.join(attempted) or 'none'}",
            code=exceptions.ErrorCode.INVALID_URI,
            context={"uri": uri, "importers": attempted},
        )

    matched_names = [imp.name for imp in matched]
    fetched = fetch_importers(matched, download_files=False)
    if not fetched:
        raise exceptions.UpstreamError(
            f"Importers failed to fetch data for URI '{uri}':"
            f" {', '.join(matched_names)}",
            code=exceptions.ErrorCode.UPSTREAM_ERROR,
            context={"uri": uri, "importers": matched_names},
        )

    merged = collect_from_importers(fetched, batch=True, use_files=False)
    if not merged.data:
        raise exceptions.BadRequestError(
            f"Importers returned no data for URI '{uri}': {', '.join(matched_names)}",
            code=exceptions.ErrorCode.IMPORTER_NO_DATA,
            context={"uri": uri, "importers": matched_names},
        )

    return ImporterFetchResponse(data=merged.data)
