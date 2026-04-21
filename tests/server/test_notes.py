from __future__ import annotations

import os
from io import BytesIO
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration


def create_test_document(
    client: TestClient,
    path: str = "test-notes-doc",
    title: str = "Test Document for Notes",
) -> tuple[str, str]:
    """Create a test document and return (papis_id, path)."""
    response = client.post(
        "/api/v1/libraries/test/documents",
        json={"title": title},
        params={"folder": path},
    )
    assert response.status_code == 201
    return response.json()["papis_id"], path


# =============================================================================
# GET /libraries/{library}/documents/{id}/notes
# =============================================================================


def test_list_notes_empty(tmp_config: TemporaryConfiguration) -> None:
    """GET .../notes returns empty list for document with no notes."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/notes")

    assert response.status_code == 200
    data = response.json()
    assert data == []


# =============================================================================
# POST /libraries/{library}/documents/{id}/notes
# =============================================================================


def test_add_note(tmp_config: TemporaryConfiguration) -> None:
    """POST .../notes adds a note to a document."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, path = create_test_document(client)

    response = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"upload": ("notes.md", BytesIO(b"# Notes"), "text/markdown")},
    )

    assert response.status_code == 201
    assert response.json() == "notes.md"

    list_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/notes")
    assert list_response.json() == ["notes.md"]

    # Verify on disk
    note_path = os.path.join(tmp_config.libdir, path, "notes.md")
    assert os.path.exists(note_path)
    assert open(note_path, "rb").read() == b"# Notes"


def test_add_note_path_normalization(tmp_config: TemporaryConfiguration) -> None:
    """POST .../notes normalizes special characters in filename."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, path = create_test_document(client)

    response = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={
            "upload": (
                "my!!notes<>with/special*chars.md",
                BytesIO(b"Content"),
                "text/markdown",
            )
        },
    )
    assert response.status_code == 201
    assert response.json() == "my-notes-with-special-chars.md"

    # Verify on disk
    note_path = os.path.join(tmp_config.libdir, path, "my-notes-with-special-chars.md")
    assert os.path.exists(note_path)


def test_add_note_when_exists(tmp_config: TemporaryConfiguration) -> None:
    """POST .../notes fails if document already has notes."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"upload": ("notes1.md", BytesIO(b"First notes"), "text/markdown")},
    )
    assert response.status_code == 201

    response = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"upload": ("notes2.md", BytesIO(b"Second notes"), "text/markdown")},
    )
    assert response.status_code == 409


def test_add_note_unique_name_suffix(tmp_config: TemporaryConfiguration) -> None:
    """POST .../notes adds suffix when filename clashes with existing file on disk."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, doc_path = create_test_document(client)

    file_on_disk = os.path.join(tmp_config.libdir, doc_path, "notes.md")
    with open(
        file_on_disk,
        "w",
        encoding="utf-8",
    ) as f:
        f.write("existing content")

    response = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"upload": ("notes.md", BytesIO(b"New content"), "text/markdown")},
    )
    assert response.status_code == 201
    assert response.json() == "notes-a.md"


def test_document_not_found(tmp_config: TemporaryConfiguration) -> None:
    """POST .../notes returns 404 when document doesn't exist."""
    from papis.server.app import app

    client = TestClient(app)

    response = client.get("/api/v1/libraries/test/documents/nonexistent-id/notes")
    assert response.status_code == 404

    response = client.post(
        "/api/v1/libraries/test/documents/nonexistent-id/notes",
        files={"upload": ("notes.md", BytesIO(b"Content"), "text/markdown")},
    )
    assert response.status_code == 404


# =============================================================================
# GET /libraries/{library}/documents/{id}/notes/{note}
# =============================================================================


def test_download_note(tmp_config: TemporaryConfiguration) -> None:
    """GET .../notes/{note} downloads a note."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"upload": ("notes.md", BytesIO(b"# My Notes"), "text/markdown")},
    )

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/notes/notes.md")

    assert response.status_code == 200
    assert response.content == b"# My Notes"


def test_download_note_not_found(tmp_config: TemporaryConfiguration) -> None:
    """GET .../notes/{note} returns 404 for non-existent note."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.get(
        f"/api/v1/libraries/test/documents/{papis_id}/notes/nonexistent.md"
    )

    assert response.status_code == 404


# =============================================================================
# PUT /libraries/{library}/documents/{id}/notes/{note}
# =============================================================================


def test_replace_note(tmp_config: TemporaryConfiguration) -> None:
    """PUT .../notes/{note} replaces note."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"upload": ("notes.md", BytesIO(b"Original content"), "text/markdown")},
    )

    response = client.put(
        f"/api/v1/libraries/test/documents/{papis_id}/notes/notes.md",
        files={"upload": ("notes.md", BytesIO(b"Updated content"), "text/markdown")},
    )

    assert response.status_code == 200
    assert response.json() == "notes.md"

    download = client.get(f"/api/v1/libraries/test/documents/{papis_id}/notes/notes.md")
    assert download.content == b"Updated content"


def test_replace_note_not_found(tmp_config: TemporaryConfiguration) -> None:
    """PUT .../notes/{note} returns 404 for non-existent note."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.put(
        f"/api/v1/libraries/test/documents/{papis_id}/notes/nonexistent.md",
        files={"upload": ("nonexistent.md", BytesIO(b"Content"), "text/markdown")},
    )

    assert response.status_code == 404


# =============================================================================
# DELETE /libraries/{library}/documents/{id}/notes/{note}
# =============================================================================


def test_delete_note(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../notes/{note} removes note from document."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, path = create_test_document(client)

    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"upload": ("notes.md", BytesIO(b"Content"), "text/markdown")},
    )

    note_path = os.path.join(tmp_config.libdir, path, "notes.md")
    assert os.path.exists(note_path)

    response = client.delete(
        f"/api/v1/libraries/test/documents/{papis_id}/notes/notes.md"
    )
    assert response.status_code == 204

    list_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/notes")
    assert list_response.json() == []

    # Verify on disk
    assert not os.path.exists(note_path)


def test_delete_note_not_found(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../notes/{note} returns 404 for non-existent note."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.delete(
        f"/api/v1/libraries/test/documents/{papis_id}/notes/nonexistent.md"
    )

    assert response.status_code == 404


# =============================================================================
# PATCH /libraries/{library}/documents/{id}/notes
# =============================================================================


def test_rename_note(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../notes renames a note."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"upload": ("old.md", BytesIO(b"Content"), "text/markdown")},
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        params={"old_note": "old.md", "new_note": "new.md"},
    )

    assert response.status_code == 200
    assert response.json() == "new.md"

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/notes")
    notes = get_response.json()
    assert notes == ["new.md"]


def test_rename_note_not_found(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../notes returns 404 when old note not in document."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        params={"old_note": "nonexistent.md", "new_note": "new.md"},
    )

    assert response.status_code == 404


def test_rename_note_path_normalization(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../notes normalizes special characters in new filename."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, path = create_test_document(client)

    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"upload": ("old.md", BytesIO(b"Content"), "text/markdown")},
    )

    old_file = os.path.join(tmp_config.libdir, path, "old.md")
    assert os.path.exists(old_file)

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        params={
            "old_note": "old.md",
            "new_note": "new!!note<>with/special*chars.md",
        },
    )
    assert response.status_code == 200

    list_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/notes")
    assert list_response.json() == ["new-note-with-special-chars.md"]

    # Verify on disk
    new_file = os.path.join(tmp_config.libdir, path, "new-note-with-special-chars.md")
    assert os.path.exists(new_file)
    assert not os.path.exists(old_file)


def test_rename_note_unique_name_suffix(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../notes adds suffix to avoid filename clashes."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, doc_path = create_test_document(client)

    response = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"upload": ("notes.md", BytesIO(b"First notes"), "text/markdown")},
    )
    assert response.status_code == 201

    file_on_disk = os.path.join(tmp_config.libdir, doc_path, "notes-clash.md")
    with open(
        file_on_disk,
        "w",
        encoding="utf-8",
    ) as f:
        f.write("some content")

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        params={"old_note": "notes.md", "new_note": "notes-clash.md"},
    )
    assert response.status_code == 200
    assert response.json() == "notes-clash-a.md"
