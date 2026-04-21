"""Cache management endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import Path, Query, Response

from papis.server import exceptions
from papis.server.routes.libraries import get_db, library_router


@library_router.delete(
    "/cache",
    tags=["Cache"],
    responses=exceptions.ResourceNotFoundError.responses(
        codes=[exceptions.ErrorCode.LIBRARY_NOT_FOUND]
    ),
)
async def clear_cache(
    library: Annotated[str, Path(description="Library name")],
    mode: Annotated[
        str,
        Query(
            description=(
                "`reset` clears and rebuilds the database, `clear` clears only."
            ),
            pattern="^(reset|clear)$",
        ),
    ] = "reset",
) -> Response:
    """Clear the document cache for a library."""
    db = get_db(library)
    db.clear()
    if mode == "reset":
        db.initialize()
        db.get_all_documents()
    return Response(status_code=204)
