"""Server-Sent Events broker and helpers."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Literal, TypedDict

if TYPE_CHECKING:
    from collections.abc import Callable

    from papis.document import Document

import papis.logging

logger = papis.logging.get_logger(__name__)


DBEventType = Literal[
    "document_added",
    "document_updated",
    "document_deleted",
    "cache_cleared",
]


class SSEEvent(TypedDict):
    """An SSE event carried over the pub/sub broker.

    ``v`` is the schema version (**not** the library or document version), ``type`` is
    one of :class:`~papis.database.base.DbChangeType` or ``"snapshot"``, ``library`` is
    the library name, and ``id`` the ``papis_id`` (or ``None``).
    """

    v: int
    type: DBEventType | Literal["snapshot"]
    library: str
    id: str | None


SubscriberQueue = asyncio.Queue[tuple[int, SSEEvent]]


class EventBroker:
    """In-process async pub/sub broker for SSE events."""

    def __init__(self) -> None:
        self._subs: dict[str, set[SubscriberQueue]] = {}
        self._lib_version: dict[str, int] = {}
        self._doc_versions: dict[str, dict[str, int]] = {}

    def get_lib_version(self, library: str) -> int:
        """Return the current library version.

        :param library: Library name.
        :returns: The library version, or 0 if unset.
        """
        return self._lib_version.get(library, 0)

    def publish(self, event: SSEEvent) -> int:
        """Publish an event to all subscribers of its library.

        Bumps the in-memory library version and fans the event out to every subscriber
        queue for the event's library. Versions reset to 0 on server restart.

        :param event: SSEEvent.
        :returns: The new library version assigned in this event.
        """
        library = event["library"]
        version = self._lib_version.get(library, 0) + 1
        self._lib_version[library] = version

        for queue in self._subs.get(library, ()):
            try:
                queue.put_nowait((version, event))
            except asyncio.QueueFull:
                # Drop oldest event to make room.
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                queue.put_nowait((version, event))
        return version

    def subscribe(self, library: str) -> SubscriberQueue:
        """Create a subscriber queue for *library*.

        :param library: Library name.
        :returns: A bounded queue that will receive ``(version, SSEEvent)`` tuples.
        """
        queue: SubscriberQueue = asyncio.Queue(maxsize=512)
        self._subs.setdefault(library, set()).add(queue)
        return queue

    def unsubscribe(self, library: str, queue: SubscriberQueue) -> None:
        """Remove a subscriber queue for *library*.

        :param library: Library name.
        :param queue: The subscriber queue to remove.
        """
        self._subs.get(library, set()).discard(queue)

    def shutdown(self) -> None:
        """Cancel all subscriptions and clear state."""
        self._subs.clear()
        self._doc_versions.clear()

    def get_doc_version(self, library: str, id: str) -> int:
        """Return the current document version.

        The version is the library version at the time of the document's last
        mutation.

        :param library: Library name.
        :param id: The document ``papis_id``.
        :returns: The document version, or 0 if unset.
        """
        return self._doc_versions.get(library, {}).get(id, 0)

    def set_doc_version(self, library: str, id: str, lib_version: int) -> None:
        """Set a document version.

        :param library: Library name.
        :param id: The document ``papis_id``.
        :param lib_version: The library version at the time of mutation.
        """
        self._doc_versions.setdefault(library, {})[id] = lib_version

    def get_document_ids_since(self, library: str, since_version: int) -> set[str]:
        """Return papis_ids with doc_version strictly greater than *since_version*.

        :param library: Library name.
        :param since_version: The version to compare against (exclusive).
        :returns: Set of ``papis_id`` strings with version > *since_version*.
        """
        lib_versions = self._doc_versions.get(library, {})
        return {pid for pid, v in lib_versions.items() if v > since_version}


def sse_frame(lib_version: int, event: SSEEvent) -> str:
    """Format an event dict as an SSE frame.

    Uses *lib_version* as the SSE ``id:`` field and ``event["type"]``
    as the ``event:`` field.  The event type is duplicated so data
    remains self-describing and ``EventSource.addEventListener`` can
    route without parsing JSON.

    :param lib_version: The library version, used as the SSE ``id:`` field.
    :param event: An SSEEvent.
    """
    return f"id: {lib_version}\nevent: {event['type']}\ndata: {json.dumps(event)}\n\n"


def make_db_callback(
    library: str,
    broker: EventBroker,
) -> Callable[[DBEventType, Document | None], None]:
    """Create a callback that bridges ``Database`` change notifications to SSE.

    Registered on each library's database instance during lifespan startup.
    Every ``db.add``, ``db.update``, ``db.delete``, and ``db.clear`` call
    automatically produces an SSE event and stores the per-document version
    on the broker.

    :param library: Library name.
    :param broker: The :class:`EventBroker` to publish to.
    :returns: A callback suitable for ``Database`` change notification.
    """

    def on_change(change_type: DBEventType, doc: Document | None) -> None:
        event: SSEEvent = {
            "v": 1,
            "type": change_type,
            "library": library,
            "id": None,
        }
        if doc is not None:
            event["id"] = doc.get("papis_id", "")

        version = broker.publish(event)

        if doc is not None and change_type != "document_deleted":
            broker.set_doc_version(library, str(doc.get("papis_id", "")), version)

    return on_change
