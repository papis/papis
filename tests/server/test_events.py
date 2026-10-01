"""Tests for the SSE event broker and the DB-change callback bridge."""

from __future__ import annotations

import json
import tempfile
from typing import TYPE_CHECKING, cast

import papis.database
from papis.document import from_data
from papis.server.events import EventBroker, make_db_callback, sse_frame

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from fastapi.testclient import TestClient

    from papis.server.events import SSEEvent
    from papis.testing import TemporaryConfiguration


def _get_broker() -> EventBroker:
    """Get the event broker from the test app state."""
    from papis.server.app import app

    broker: EventBroker = app.state.broker
    return broker


def test_broker_version_starts_at_zero() -> None:
    """A fresh broker has version 0 for a library with no published events."""
    broker = EventBroker()
    assert broker.get_lib_version("papers") == 0


def test_broker_publish_bumps_version() -> None:
    """publish() bumps the library version and returns it."""
    broker = EventBroker()
    event: SSEEvent = {
        "v": 1,
        "type": "document_added",
        "library": "papers",
        "id": None,
    }
    version = broker.publish(event)
    assert version == 1
    assert broker.get_lib_version("papers") == 1


def test_broker_publish_fans_out_to_subscribers() -> None:
    """Subscribers receive events published after they subscribed."""
    broker = EventBroker()
    q = broker.subscribe("papers")

    event: SSEEvent = {
        "v": 1,
        "type": "document_added",
        "library": "papers",
        "id": "doc-123",
    }
    version = broker.publish(event)

    assert q.qsize() == 1
    got_version, got_event = q.get_nowait()
    assert got_version == version
    assert got_event == event


def test_broker_does_not_cross_libraries() -> None:
    """Events for library A do not reach subscribers of library B."""
    broker = EventBroker()
    q_a = broker.subscribe("papers")
    q_b = broker.subscribe("books")

    broker.publish({"v": 1, "type": "document_added", "library": "papers", "id": None})
    assert q_a.qsize() == 1
    assert q_b.qsize() == 0


def test_broker_multiple_subscribers_same_library() -> None:
    """Multiple subscribers for the same library all receive the event."""
    broker = EventBroker()
    q1 = broker.subscribe("papers")
    q2 = broker.subscribe("papers")

    broker.publish({"v": 1, "type": "document_added", "library": "papers", "id": None})
    assert q1.qsize() == 1
    assert q2.qsize() == 1


def test_broker_unsubscribe_stops_events() -> None:
    """After unsubscribe, no further events are received."""
    broker = EventBroker()
    q = broker.subscribe("papers")
    broker.publish({"v": 1, "type": "document_added", "library": "papers", "id": None})
    assert q.qsize() == 1
    q.get_nowait()

    broker.unsubscribe("papers", q)
    broker.publish({"v": 1, "type": "document_added", "library": "papers", "id": None})
    assert q.qsize() == 0


def test_broker_publish_drops_oldest_when_queue_full() -> None:
    """A full subscriber queue drops its oldest event to make room."""
    broker = EventBroker()
    q = broker.subscribe("papers")

    # the subscriber queue capacity is 512
    for i in range(1, 514):
        event: SSEEvent = {
            "v": 1,
            "type": "document_added",
            "library": "papers",
            "id": f"doc-{i}",
        }
        broker.publish(event)

    assert q.qsize() == 512

    versions: list[int] = []
    while not q.empty():
        version, _ = q.get_nowait()
        versions.append(version)

    assert versions[0] == 2
    assert versions[-1] == 513
    assert len(versions) == 512


def test_db_mutations_update_broker_versions(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """Database mutations bump library and per-document versions via the callback."""
    db = papis.database.get()
    broker = _get_broker()

    doc = from_data({"author": "Bridge Author", "title": "Bridge Title"})
    folder = tempfile.mkdtemp(dir=tmp_config.tmpdir)
    doc.set_folder(folder)
    doc.save()
    db.add(doc)

    add_version = broker.get_lib_version("test")
    assert add_version >= 1
    doc_id = str(doc["papis_id"])
    assert broker.get_doc_version("test", doc_id) == add_version

    doc["title"] = "Bridge Updated"
    doc.save()
    db.update(doc)

    update_version = broker.get_lib_version("test")
    assert update_version > add_version
    assert broker.get_doc_version("test", doc_id) == update_version

    db.delete(doc)
    assert broker.get_lib_version("test") > update_version
    # ``document_deleted`` does not reset the per-document version
    assert broker.get_doc_version("test", doc_id) == update_version


def test_db_callback_handles_missing_document(client: TestClient) -> None:
    """``make_db_callback`` publishes ``id: null`` events without a document."""
    broker = _get_broker()
    q = broker.subscribe("test")

    version_before = broker.get_lib_version("test")
    callback = make_db_callback("test", broker)
    callback("cache_cleared", None)

    assert broker.get_lib_version("test") > version_before
    _, event = q.get_nowait()
    assert event["type"] == "cache_cleared"
    assert event["id"] is None

    broker.unsubscribe("test", q)


def test_clear_cache_publishes_cache_cleared_event(
    client: TestClient,
) -> None:
    """DELETE /cache publishes a ``cache_cleared`` event to the broker."""
    broker = _get_broker()
    q = broker.subscribe("test")

    client.delete("/api/v1/libraries/test/cache")

    assert q.qsize() == 1
    _, event = q.get_nowait()
    assert event["type"] == "cache_cleared"
    assert event["library"] == "test"
    assert event["id"] is None

    broker.unsubscribe("test", q)


def test_sse_frame_format() -> None:
    """``sse_frame`` produces a valid SSE frame with id, event, and data."""
    event: SSEEvent = {
        "v": 1,
        "type": "snapshot",
        "library": "test",
        "id": None,
    }
    frame = sse_frame(7, event)

    lines = frame.split("\n")
    assert "id: 7" in lines
    assert "event: snapshot" in lines
    assert frame.endswith("\n\n")
    data_line = next(line for line in lines if line.startswith("data: "))
    parsed = json.loads(data_line[6:])
    assert parsed == event


def _frame_data(frame: str) -> dict[str, object]:
    """Parse the JSON payload of an SSE frame."""
    data_line = next(line for line in frame.split("\n") if line.startswith("data: "))
    data = json.loads(data_line[6:])
    assert isinstance(data, dict)
    return data


def test_events_endpoint_streams_frames(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET .../events streams a snapshot frame, then mutation frames.

    We can't use the TestClient since it buffers the entire response body and cannot
    represent an SSE stream. The ``client`` fixture is needed for the lifespan that
    creates the broker and registers the DB change callback.
    """
    import asyncio

    from starlette.requests import Request

    from papis.server.app import app
    from papis.server.routes.events import events

    async def _main() -> None:
        broker = _get_broker()

        request = Request({
            "type": "http",
            "method": "GET",
            "path": "/api/v1/libraries/test/events",
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("testclient", 50000),
            "app": app,
        })
        response = await events(request, library="test")
        assert response.media_type == "text/event-stream"
        # the route always passes an async generator, so aclose() is safe
        body = cast("AsyncGenerator[str, None]", response.body_iterator)

        # first frame: a snapshot of the current library state
        frame = _frame_data(await asyncio.wait_for(anext(body), timeout=5))
        assert frame["type"] == "snapshot"
        assert frame["library"] == "test"
        assert frame["id"] is None

        # a database mutation produces a document_added frame
        db = papis.database.get()
        doc = from_data({"author": "Stream Author", "title": "Stream Title"})
        folder = tempfile.mkdtemp(dir=tmp_config.tmpdir)
        doc.set_folder(folder)
        doc.save()
        db.add(doc)

        frame = _frame_data(await asyncio.wait_for(anext(body), timeout=5))
        assert frame["type"] == "document_added"
        assert frame["library"] == "test"
        assert frame["id"] == str(doc["papis_id"])

        # closing the stream unsubscribes the queue from the broker
        await body.aclose()
        assert not broker._subs.get("test")

    asyncio.run(_main())
