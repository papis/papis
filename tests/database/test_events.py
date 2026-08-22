"""Tests for database change notification callbacks.

The event sequences are backend-specific (e.g. Whoosh has no native update and fires
``document_deleted`` followed by ``document_added``), so the expectations are specific
to backend.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, TypedDict

import pytest

import papis.database
from papis.document import from_data
from papis.exceptions import DocumentFolderNotFound

if TYPE_CHECKING:
    from papis.database.base import Database
    from papis.document import Document
    from papis.testing import TemporaryLibrary

PAPIS_DB_BACKENDS = ["papis", "sqlite"]

try:
    import whoosh  # ruff:ignore[unused-import]

    PAPIS_DB_BACKENDS.append("whoosh")
except ImportError:
    pass

PAPIS_DB_SETTINGS = [{"settings": {"database-backend": b}} for b in PAPIS_DB_BACKENDS]


class EventExpectations(TypedDict):
    """Per-backend expectations for callback event sequences."""

    update_types: list[str]
    add_no_folder_error: type[Exception]
    delete_missing_error: type[Exception] | None


PAPIS_DB_EVENTS: dict[str, EventExpectations] = {
    "papis": {
        "update_types": ["document_updated"],
        "add_no_folder_error": ValueError,
        "delete_missing_error": ValueError,
    },
    "sqlite": {
        "update_types": ["document_updated"],
        "add_no_folder_error": DocumentFolderNotFound,
        "delete_missing_error": DocumentFolderNotFound,
    },
    "whoosh": {
        # Whoosh has no native update: it deletes and re-adds the document.
        "update_types": ["document_deleted", "document_added"],
        "add_no_folder_error": DocumentFolderNotFound,
        # Deleting a missing document is a silent no-op.
        "delete_missing_error": None,
    },
}


def _expectations(db: Database) -> EventExpectations:
    """Return the event expectations for *db*'s backend."""
    return PAPIS_DB_EVENTS[db.get_backend_name()]


def _new_doc(tmp_library: TemporaryLibrary, relfolder: str) -> Document:
    """Create and save a document in the library at *relfolder*."""
    folder = os.path.join(tmp_library.libdir, relfolder)
    os.makedirs(folder, exist_ok=True)
    doc = from_data({"author": "Event Author", "title": "Event Title"})
    doc.set_folder(folder)
    doc.save()
    return doc


@pytest.mark.parametrize(
    "tmp_library", PAPIS_DB_SETTINGS, indirect=True, ids=PAPIS_DB_BACKENDS
)
def test_add_fires_document_added_callback(
    tmp_library: TemporaryLibrary,
) -> None:
    """db.add() fires a ``document_added`` callback with the document."""
    db = papis.database.get()

    events: list[tuple[str, Document | None]] = []
    db.set_on_change_callback(lambda t, d: events.append((t, d)))

    doc = _new_doc(tmp_library, "event-add")
    db.add(doc)

    assert len(events) == 1
    assert events[0][0] == "document_added"
    assert events[0][1] is doc


@pytest.mark.parametrize(
    "tmp_library", PAPIS_DB_SETTINGS, indirect=True, ids=PAPIS_DB_BACKENDS
)
def test_update_fires_expected_events(tmp_library: TemporaryLibrary) -> None:
    """db.update() fires the backend's update event sequence."""
    db = papis.database.get()

    doc = _new_doc(tmp_library, "event-update")
    db.add(doc)

    events: list[tuple[str, Document | None]] = []
    db.set_on_change_callback(lambda t, d: events.append((t, d)))

    doc["title"] = "Updated Event Title"
    doc.save()
    db.update(doc)

    assert [t for t, _ in events] == _expectations(db)["update_types"]
    assert all(d is doc for _, d in events)


@pytest.mark.parametrize(
    "tmp_library", PAPIS_DB_SETTINGS, indirect=True, ids=PAPIS_DB_BACKENDS
)
def test_delete_fires_document_deleted_callback(
    tmp_library: TemporaryLibrary,
) -> None:
    """db.delete() fires a ``document_deleted`` callback with the document."""
    db = papis.database.get()

    doc = _new_doc(tmp_library, "event-delete")
    db.add(doc)

    events: list[tuple[str, Document | None]] = []
    db.set_on_change_callback(lambda t, d: events.append((t, d)))

    db.delete(doc)

    assert len(events) == 1
    assert events[0][0] == "document_deleted"
    assert events[0][1] is doc


@pytest.mark.parametrize(
    "tmp_library", PAPIS_DB_SETTINGS, indirect=True, ids=PAPIS_DB_BACKENDS
)
def test_add_without_folder_fires_no_callback(
    tmp_library: TemporaryLibrary,
) -> None:
    """db.add() on a folderless document raises without firing a callback."""
    db = papis.database.get()

    events: list[tuple[str, Document | None]] = []
    db.set_on_change_callback(lambda t, d: events.append((t, d)))

    doc = from_data({"author": "Event Author", "title": "Folderless"})
    with pytest.raises(_expectations(db)["add_no_folder_error"]):
        db.add(doc)

    assert events == []


@pytest.mark.parametrize(
    "tmp_library", PAPIS_DB_SETTINGS, indirect=True, ids=PAPIS_DB_BACKENDS
)
def test_delete_missing_document(tmp_library: TemporaryLibrary) -> None:
    """db.delete() of a document not in the database raise (except whoosh)."""
    db = papis.database.get()

    events: list[tuple[str, Document | None]] = []
    db.set_on_change_callback(lambda t, d: events.append((t, d)))

    doc = _new_doc(tmp_library, "event-ghost")
    doc["papis_id"] = "ghost-id"
    doc.save()

    expectations = _expectations(db)
    error = expectations["delete_missing_error"]
    if error is None:
        db.delete(doc)
    else:
        with pytest.raises(error):
            db.delete(doc)


@pytest.mark.parametrize(
    "tmp_library", PAPIS_DB_SETTINGS, indirect=True, ids=PAPIS_DB_BACKENDS
)
def test_clear_fires_no_callback(tmp_library: TemporaryLibrary) -> None:
    """db.clear() does not fire a callback (handled in API server)."""
    db = papis.database.get()

    events: list[tuple[str, Document | None]] = []
    db.set_on_change_callback(lambda t, d: events.append((t, d)))

    db.clear()

    assert events == []
