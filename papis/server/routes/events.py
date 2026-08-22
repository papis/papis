"""Server-Sent Events endpoint."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Annotated

from fastapi import Path, Request
from fastapi.responses import StreamingResponse

import papis.logging
from papis.server import exceptions
from papis.server.events import sse_frame
from papis.server.routes.libraries import library_router

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from papis.server.events import EventBroker

logger = papis.logging.get_logger(__name__)


@library_router.get(
    "/events",
    tags=["Libraries"],
    response_class=StreamingResponse,
    responses=exceptions.ResourceNotFoundError.responses(
        types=[exceptions.ErrorCode.LIBRARY_NOT_FOUND]
    ),
)
async def events(
    request: Request,
    library: Annotated[str, Path(description="Library name")],
) -> StreamingResponse:
    """Subscribe to live events for a library via Server-Sent Events.

    Events are *hints* that inform the client what resources should be re-fetched.

    **Wire format**. Each SSE frame has:

        id: <library-version>
        event: <event-type>
        data: <json-payload>

    **JSON payload schema**:

        {
            "v": 1,             # schema version
            "type": "...",      # event type (see below)
            "library": "...",   # library name
            "id": null | "..."  # papis_id, or null if not applicable
        }

    **Event types**:

        snapshot           Sent once on connect.
        document_added     A document was created.
        document_updated   A document's ``info.yaml`` was modified.
        document_deleted   A document was removed.
        cache_cleared      The library database was cleared.

    **Lifecycle**:

        1. Client opens the stream and receives a ``snapshot`` event with the current
           library version.
        2. Mutation events follow as they occur. Each event's ``id`` field is the new
           library version.
        3. If the client reconnects, it receives a fresh ``snapshot``.  It must re-fetch
           all documents as the ``id`` resets to 0 on server restart, rendering client
           state stale.
    """

    broker: EventBroker = request.app.state.broker

    async def event_generator() -> AsyncIterator[str]:
        queue = broker.subscribe(library)
        try:
            version = broker.get_lib_version(library)
            yield sse_frame(
                version,
                {
                    "v": 1,
                    "type": "snapshot",
                    "library": library,
                    "id": None,
                },
            )
            while True:
                version, event = await queue.get()
                yield sse_frame(version, event)
        except (asyncio.CancelledError, GeneratorExit):
            # Client disconnected — the finally block runs to unsubscribe.
            pass
        finally:
            broker.unsubscribe(library, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
