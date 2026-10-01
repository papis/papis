"""Cache management endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import Path, Query, Request, Response

from papis.server import exceptions
from papis.server.routes.libraries import get_db, library_router

if TYPE_CHECKING:
    from papis.server.events import EventBroker


@library_router.delete(
    "/cache",
    tags=["Cache"],
    responses=exceptions.ResourceNotFoundError.responses(
        types=[exceptions.ErrorCode.LIBRARY_NOT_FOUND]
    ),
)
async def clear_cache(
    request: Request,
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

    broker: EventBroker = request.app.state.broker
    broker.publish({
        "v": 1,
        "type": "cache_cleared",
        "library": library,
        "id": None,
    })
    return Response(status_code=204)
