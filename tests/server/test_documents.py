from __future__ import annotations

import os
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration


def create_test_document(
    client: TestClient,
    path: str = "test-doc",
    title: str = "Test Document",
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
# GET /libraries/{library}/documents
# =============================================================================


def test_get_documents_empty(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents returns empty list when library has no documents."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries/test/documents")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_documents_with_query(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents with query returns only matching documents."""
    from papis.server.app import app

    client = TestClient(app)
    create_test_document(client, path="query-test-1", title="Find this doc")
    create_test_document(client, path="query-test-2", title="Not this doc")

    response = client.get(
        "/api/v1/libraries/test/documents", params={"q": "title:'Find this doc'"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Find this doc"


def test_get_documents_library_not_found(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents returns 404 for non-existent library."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries/nonexistent/documents")

    assert response.status_code == 404


def test_get_document_folder_not_found(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents/{id}/folder returns 404 when folder is missing."""
    import shutil

    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="test-doc")

    doc_folder = os.path.join(tmp_config.libdir, "test-doc")
    shutil.rmtree(doc_folder)

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/folder")
    assert response.status_code == 404


# =============================================================================
# POST /libraries/{library}/documents
# =============================================================================


def test_create_document(tmp_config: TemporaryConfiguration) -> None:
    """POST .../documents creates a new document."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="test-doc", title="Test Document")

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Document"

    # Verify on disk
    path_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/folder")
    assert path_response.status_code == 200
    doc_folder = os.path.join(tmp_config.libdir, path_response.json())
    assert os.path.exists(doc_folder)


def test_create_document_with_extra_fields(tmp_config: TemporaryConfiguration) -> None:
    """POST .../documents accepts fields not explicitly defined."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/libraries/test/documents",
        json={"title": "Test", "custom_field": "custom_value"},
        params={"folder": "test-extra"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test"
    assert data["custom_field"] == "custom_value"


def test_create_document_in_subfolder(tmp_config: TemporaryConfiguration) -> None:
    """POST .../documents creates document in subfolders."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(
        client, path="subfolder/nested/test", title="Subfolder Test"
    )

    path_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/folder")
    assert path_response.status_code == 200
    assert path_response.json() == "subfolder/nested/test"

    # Verify on disk
    doc_folder = os.path.join(tmp_config.libdir, "subfolder", "nested", "test")
    assert os.path.exists(doc_folder)


def test_create_document_illegal_path(tmp_config: TemporaryConfiguration) -> None:
    """POST .../documents can't escape library root folder."""
    from papis.server.app import app

    client = TestClient(app)

    illegal_paths = [
        "../outside-library",
        "../../etc/passwd",
        "subfolder/../../outside",
        # NOTE: "/absolute/path" is NOT included here because
        # normalize_doc_path strips the leading "/" resulting in
        # "absolute/path" which is a valid subfolder within the library.
    ]

    for path in illegal_paths:
        response = client.post(
            "/api/v1/libraries/test/documents",
            json={"title": "Illegal Path Test"},
            params={"folder": path},
        )
        assert response.status_code == 400


def test_create_document_library_not_found(tmp_config: TemporaryConfiguration) -> None:
    """POST .../documents returns 404 for non-existent library."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/libraries/nonexistent/documents",
        json={"title": "Test"},
        params={"folder": "test"},
    )

    assert response.status_code == 404


def test_create_document_path_normalization(tmp_config: TemporaryConfiguration) -> None:
    """POST .../documents paths with special characters are normalized."""
    from papis.server.app import app

    client = TestClient(app)

    create_response = client.post(
        "/api/v1/libraries/test/documents",
        json={"title": "Special Chars Test"},
        params={"folder": "test!!folder<>with/special*chars"},
    )
    assert create_response.status_code == 201
    papis_id = create_response.json()["papis_id"]

    path_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/folder")
    assert path_response.json() == "test-folder-with/special-chars"


def test_create_document_unique_path_suffix(tmp_config: TemporaryConfiguration) -> None:
    """POST .../documents creates unique folder names with suffix."""
    from papis.server.app import app

    client = TestClient(app)

    response1 = client.post(
        "/api/v1/libraries/test/documents",
        json={"title": "First Doc"},
        params={"folder": "test-path"},
    )
    assert response1.status_code == 201
    path1 = client.get(
        f"/api/v1/libraries/test/documents/{response1.json()['papis_id']}/folder"
    ).json()

    response2 = client.post(
        "/api/v1/libraries/test/documents",
        json={"title": "Second Doc"},
        params={"folder": "test-path"},
    )
    assert response2.status_code == 201
    path2 = client.get(
        f"/api/v1/libraries/test/documents/{response2.json()['papis_id']}/folder"
    ).json()

    assert path1 == "test-path"
    assert path2 == "test-path-a"


def test_create_document_rejects_files_and_notes(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST .../documents rejects requests with files or notes fields."""
    from papis.server.app import app

    client = TestClient(app)

    response = client.post(
        "/api/v1/libraries/test/documents",
        json={"title": "Test", "files": ["file.pdf"]},
        params={"folder": "test"},
    )
    assert response.status_code == 400

    response = client.post(
        "/api/v1/libraries/test/documents",
        json={"title": "Test", "notes": "some notes"},
        params={"folder": "test"},
    )
    assert response.status_code == 400


# =============================================================================
# GET /libraries/{library}/documents/{id}
# =============================================================================


def test_get_document(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents/{id} returns a specific document by ID."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="get-test", title="Get Test")

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Get Test"
    assert data["papis_id"] == papis_id


def test_get_document_not_found(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents/{id} returns 404 for non-existent document."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries/test/documents/nonexistent-id")

    assert response.status_code == 404


# =============================================================================
# PATCH /libraries/{library}/documents/{id}
# =============================================================================


def test_update_document(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../documents/{id} updates document metadata."""
    import papis.document
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(
        client, path="update-test", title="Original Title"
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"title": "Updated Title"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    get_data = get_response.json()
    assert get_data["title"] == "Updated Title"

    # Verify on disk
    path_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/folder")
    doc_folder = os.path.join(tmp_config.libdir, path_response.json())
    doc_on_disk = papis.document.Document(folder=doc_folder)
    assert doc_on_disk["title"] == "Updated Title"


def test_update_document_delete_field(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../documents/{id} can delete a field."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(
        client, path="delete-field-test", title="Delete Field Test"
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"author": "Author To Delete"},
    )
    assert response.status_code == 200

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"author": None},
    )

    assert response.status_code == 200

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    get_data = get_response.json()
    assert "author" not in get_data


def test_update_document_add_field(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../documents/{id} can add new fields."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(
        client, path="add-field-test", title="Add Field Test"
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"author": "New Author", "year": 2024},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["author"] == "New Author"
    assert data["year"] == 2024


def test_update_document_not_found(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../documents/{id} returns 404 for non-existent document."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.patch(
        "/api/v1/libraries/test/documents/nonexistent-id",
        json={"title": "New Title"},
    )

    assert response.status_code == 404


def test_update_document_rejects_files_and_notes(
    tmp_config: TemporaryConfiguration,
) -> None:
    """PATCH .../documents/{id} rejects requests that modify files or notes."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="reject-test", title="Reject Test")

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"files": ["file.pdf"]},
    )
    assert response.status_code == 400

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"notes": "some notes"},
    )
    assert response.status_code == 400


# =============================================================================
# DELETE /libraries/{library}/documents/{id}
# =============================================================================


def test_delete_document(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../documents/{id} deletes document folder from disk."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="delete-test", title="Delete Test")

    path_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/folder")
    assert path_response.status_code == 200
    doc_folder = os.path.join(tmp_config.libdir, path_response.json())
    assert os.path.exists(doc_folder)

    response = client.delete(f"/api/v1/libraries/test/documents/{papis_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    assert get_response.status_code == 404

    assert not os.path.exists(doc_folder)


def test_delete_document_not_found(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../documents/{id} returns 404 for non-existent document."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.delete("/api/v1/libraries/test/documents/nonexistent-id")

    assert response.status_code == 404


# =============================================================================
# GET /libraries/{library}/documents/{id}/folder
# =============================================================================


def test_get_document_path(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents/{id}/folder returns the document folder."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="path-test", title="Path Test")

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/folder")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, str)
    assert "path-test" in data


def test_get_document_path_not_found(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents/{id}/folder returns 404 for non-existent document."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries/test/documents/nonexistent-id/folder")

    assert response.status_code == 404


# =============================================================================
# PATCH /libraries/{library}/documents/{id}/folder
# =============================================================================


def test_move_document(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../documents/{id}/folder moves document to new location."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="original-path", title="Move Test")

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/folder",
        params={"folder": "new-location/moved-doc"},
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, str)
    assert "new-location" in data
    assert "moved-doc" in data

    # Verify on disk
    lib_path = tmp_config.libdir
    new_folder = os.path.join(lib_path, data)
    assert os.path.exists(new_folder)
    assert os.path.exists(os.path.join(new_folder, "info.yaml"))
    old_folder = os.path.join(lib_path, "original-path")
    assert not os.path.exists(old_folder)


def test_move_document_not_found(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../documents/{id}/folder returns 404 for non-existent document."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.patch(
        "/api/v1/libraries/test/documents/nonexistent-id/folder",
        params={"folder": "new-path"},
    )

    assert response.status_code == 404


def test_move_document_path_normalization(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../documents/{id}/folder normalizes special chars to safe folder names."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(
        client, path="original-path", title="Move Normalize Test"
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}/folder",
        params={"folder": "new!!path<>with/special*chars"},
    )
    assert response.status_code == 200

    assert response.json() == "new-path-with/special-chars"


def test_move_document_unique_path_suffix(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../documents/{id}/folder adds suffix when clashes arise."""
    from papis.server.app import app

    client = TestClient(app)

    create_test_document(client, path="target-path", title="First")
    papis_id2, _ = create_test_document(client, path="other-path", title="Second")

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id2}/folder",
        params={"folder": "target-path"},
    )
    assert response.status_code == 200

    path = response.json()
    assert path == "target-path-a"
