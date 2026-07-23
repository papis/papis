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
    import json

    response = client.post(
        "/api/v1/libraries/test/documents",
        data={"data": json.dumps({"title": title}), "folder": path},
    )
    assert response.status_code == 201
    return response.json()["document"]["papis_id"], path


# =============================================================================
# GET /libraries/{library}/documents/{id}/notes
# =============================================================================


def test_download_note_not_found(tmp_config: TemporaryConfiguration) -> None:
    """GET .../notes returns 404 for document with no notes."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/notes")

    assert response.status_code == 404


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
    )

    assert response.status_code == 201
    assert response.json()["name"] == "notes.tex"

    # Verify on disk
    note_path = os.path.join(tmp_config.libdir, path, "notes.tex")
    assert os.path.exists(note_path)


def test_add_note_with_template(tmp_config: TemporaryConfiguration) -> None:
    """POST .../notes generates content from notes-template."""
    import papis.config
    from papis.server.app import app

    client = TestClient(app)
    papis_id, path = create_test_document(client)

    # Create a template file
    template_path = os.path.join(tmp_config.tmpdir, "notes.tmpl")
    with open(template_path, "w", encoding="utf-8") as f:
        f.write("Title: {doc[title]}")
    papis.config.set("notes-template", template_path)

    response = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
    )

    assert response.status_code == 201
    assert response.json()["name"] == "notes.tex"

    # Verify on disk
    note_path = os.path.join(tmp_config.libdir, path, "notes.tex")
    assert os.path.exists(note_path)
    with open(note_path, encoding="utf-8") as f:
        content = f.read()
    assert "Title: Test Document for Notes" in content


def test_add_note_when_exists(tmp_config: TemporaryConfiguration) -> None:
    """POST .../notes fails if document already has notes."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
    )
    assert response.status_code == 201

    response = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
    )
    assert response.status_code == 409


def test_add_note_file_already_on_disk(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST .../notes succeeds when notes file already on disk but not in metadata.

    FIXME: This is the case because we're using Papis core's `note_path_ensured()`,
    which has this behaviour. We might want to implement unique path generation as for
    files. Test is here to catch any changes in behaviour.
    """
    from papis.server.app import app

    client = TestClient(app)
    papis_id, doc_path = create_test_document(client)

    file_on_disk = os.path.join(tmp_config.libdir, doc_path, "notes.tex")
    with open(file_on_disk, "w", encoding="utf-8") as f:
        f.write("existing content")

    response = client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
    )
    assert response.status_code == 201
    assert response.json()["name"] == "notes.tex"
    with open(file_on_disk, encoding="utf-8") as f:
        assert f.read() == "existing content"


def test_document_not_found(tmp_config: TemporaryConfiguration) -> None:
    """Endpoints return 404 when document doesn't exist."""
    from papis.server.app import app

    client = TestClient(app)

    response = client.post("/api/v1/libraries/test/documents/nonexistent-id/notes")
    assert response.status_code == 404


# =============================================================================
# GET /libraries/{library}/documents/{id}/notes  (download)
# =============================================================================


def test_download_note(tmp_config: TemporaryConfiguration) -> None:
    """GET .../notes downloads a note."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    client.post(f"/api/v1/libraries/test/documents/{papis_id}/notes")
    client.put(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"file_upload": ("notes.tex", BytesIO(b"# My Notes"), "text/markdown")},
    )

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/notes")

    assert response.status_code == 200
    assert response.content == b"# My Notes"


# =============================================================================
# PUT /libraries/{library}/documents/{id}/notes
# =============================================================================


def test_replace_note(tmp_config: TemporaryConfiguration) -> None:
    """PUT .../notes replaces note content."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    client.post(f"/api/v1/libraries/test/documents/{papis_id}/notes")
    client.put(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={
            "file_upload": ("notes.tex", BytesIO(b"Original content"), "text/markdown")
        },
    )

    response = client.put(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={
            "file_upload": ("notes.tex", BytesIO(b"Updated content"), "text/markdown")
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "notes.tex"

    download = client.get(f"/api/v1/libraries/test/documents/{papis_id}/notes")
    assert download.content == b"Updated content"


def test_replace_note_not_found(tmp_config: TemporaryConfiguration) -> None:
    """PUT .../notes returns 404 for document with no notes."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.put(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"file_upload": ("notes.tex", BytesIO(b"Content"), "text/markdown")},
    )

    assert response.status_code == 404


# =============================================================================
# DELETE /libraries/{library}/documents/{id}/notes
# =============================================================================


def test_delete_note(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../notes removes note from document."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, path = create_test_document(client)

    client.post(f"/api/v1/libraries/test/documents/{papis_id}/notes")
    client.put(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"file_upload": ("notes.tex", BytesIO(b"Content"), "text/markdown")},
    )

    note_path = os.path.join(tmp_config.libdir, path, "notes.tex")
    assert os.path.exists(note_path)

    response = client.delete(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
    )
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/notes")
    assert get_response.status_code == 404

    # Verify on disk
    assert not os.path.exists(note_path)


def test_delete_note_missing_on_disk(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../notes cleans up metadata even when note is gone from disk."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, doc_path = create_test_document(
        client, path="delete-stale-note", title="Delete Stale Note"
    )

    client.post(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
    )
    os.unlink(os.path.join(tmp_config.libdir, doc_path, "notes.tex"))

    response = client.delete(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
    )
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/notes")
    assert get_response.status_code == 404


def test_delete_note_not_found(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../notes returns 404 for document with no notes."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.delete(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
    )

    assert response.status_code == 404


# =============================================================================
# PATCH /libraries/{library}/documents/{id}/notes
# =============================================================================


def test_rename_note(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../notes renames a note."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, path = create_test_document(client)

    client.post(f"/api/v1/libraries/test/documents/{papis_id}/notes")
    client.put(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"file_upload": ("notes.tex", BytesIO(b"Content"), "text/markdown")},
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        json={"filename": "new.md"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "new.md"

    # Verify on disk
    old_file = os.path.join(tmp_config.libdir, path, "notes.tex")
    new_file = os.path.join(tmp_config.libdir, path, "new.md")
    assert not os.path.exists(old_file)
    assert os.path.exists(new_file)


def test_rename_note_self_rename(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../notes returns the same name when renaming to itself."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, path = create_test_document(client)

    content = b"Original note content"
    client.post(f"/api/v1/libraries/test/documents/{papis_id}/notes")
    client.put(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"file_upload": ("notes.tex", BytesIO(content), "text/markdown")},
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        json={"filename": "notes.tex"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "notes.tex"

    # Verify on disk
    file_path = os.path.join(tmp_config.libdir, path, "notes.tex")
    assert os.path.exists(file_path)
    with open(file_path, "rb") as f:
        assert f.read() == content


def test_rename_note_body_wins_over_config(
    tmp_config: TemporaryConfiguration,
) -> None:
    """PATCH .../notes explicit body takes priority over notes-name config."""
    import papis.config
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    client.post(f"/api/v1/libraries/test/documents/{papis_id}/notes")
    client.put(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"file_upload": ("notes.tex", BytesIO(b"Content"), "text/plain")},
    )

    papis.config.set("notes-name", "config-note.tex")

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        json={"filename": "body-wins.tex"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "body-wins.tex"


def test_rename_note_not_found(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../notes returns 404 for document with no notes."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client)

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        json={"filename": "new.md"},
    )

    assert response.status_code == 404


def test_rename_note_path_normalization(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../notes normalizes special characters in new filename."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, path = create_test_document(client)

    client.post(f"/api/v1/libraries/test/documents/{papis_id}/notes")
    client.put(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"file_upload": ("notes.tex", BytesIO(b"Content"), "text/markdown")},
    )

    old_file = os.path.join(tmp_config.libdir, path, "notes.tex")
    assert os.path.exists(old_file)

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        json={"filename": "new!!note<>with/special*chars.md"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "new-note-with-special-chars.md"

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
    )
    assert response.status_code == 201
    client.put(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        files={"file_upload": ("notes.tex", BytesIO(b"First notes"), "text/markdown")},
    )

    file_on_disk = os.path.join(tmp_config.libdir, doc_path, "notes-clash.md")
    with open(file_on_disk, "w", encoding="utf-8") as f:
        f.write("some content")

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/notes",
        json={"filename": "notes-clash.md"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "notes-clash-a.md"
