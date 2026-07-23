from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration


def create_test_document(
    client: TestClient,
    path: str = "test-doc",
    title: str = "Test Document",
    **kwargs: object,
) -> tuple[str, str]:
    """Create a test document and return (papis_id, path)."""
    body: dict[str, object] = {"title": title, **kwargs}
    response = client.post(
        "/api/v1/libraries/test/documents",
        data={"data": json.dumps(body), "folder": path},
    )
    assert response.status_code == 201
    return response.json()["document"]["papis_id"], path


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
    assert isinstance(data["documents"], list)
    assert len(data["documents"]) == 0


def test_get_documents_with_query(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents with query returns only matching documents."""
    from papis.server.app import app

    client = TestClient(app)
    create_test_document(client, path="query-test-1", title="Find this doc")
    create_test_document(client, path="query-test-2", title="Not this doc")

    response = client.get("/api/v1/libraries/test/documents", params={"q": "Find"})

    assert response.status_code == 200
    data = response.json()
    docs = data["documents"]
    assert len(docs) == 1
    assert docs[0]["title"] == "Find this doc"


def test_get_documents_library_not_found(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents returns 404 for non-existent library."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries/nonexistent/documents")

    assert response.status_code == 404


def test_get_document_folder_not_found(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents returns 404 when folder is missing."""
    import shutil

    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="test-doc")

    doc_folder = os.path.join(tmp_config.libdir, "test-doc")
    shutil.rmtree(doc_folder)

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
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
    data = response.json()["document"]
    assert data["title"] == "Test Document"

    # Verify on disk
    doc_folder = os.path.join(tmp_config.libdir, response.json()["folder"])
    assert os.path.exists(doc_folder)


def test_create_document_generates_ref(tmp_config: TemporaryConfiguration) -> None:
    """POST .../documents auto-generates a bibtex ref when not provided."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/libraries/test/documents",
        data={
            "data": json.dumps({"title": "Ref Test", "author": "Someone"}),
            "folder": "ref-test",
        },
    )

    assert response.status_code == 201
    data = response.json()["document"]
    assert "ref" in data
    assert data["ref"] != ""


def test_create_document_new_failure_returns_500(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST .../documents returns 500 when new() fails."""
    from unittest.mock import patch

    import papis.document
    from papis.server.app import app

    client = TestClient(app, raise_server_exceptions=False)

    with patch.object(papis.document, "new", side_effect=ValueError("new failed")):
        response = client.post(
            "/api/v1/libraries/test/documents",
            data={"data": '{"title": "Fail Test"}', "folder": "fail-path"},
        )

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert detail["code"] == "internal_server_error"


def test_create_document_with_extra_fields(tmp_config: TemporaryConfiguration) -> None:
    """POST .../documents accepts fields not explicitly defined."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/libraries/test/documents",
        data={
            "data": json.dumps({"title": "Test", "custom_field": "custom_value"}),
            "folder": "test-extra",
        },
    )

    assert response.status_code == 201
    data = response.json()["document"]
    assert data["title"] == "Test"
    assert data["custom_field"] == "custom_value"


def test_create_document_in_subfolder(tmp_config: TemporaryConfiguration) -> None:
    """POST .../documents creates document in subfolders."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(
        client, path="subfolder/nested/test", title="Subfolder Test"
    )

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    assert get_response.status_code == 200
    assert get_response.json()["folder"] == "subfolder/nested/test"

    # Verify on disk
    doc_folder = os.path.join(tmp_config.libdir, "subfolder", "nested", "test")
    assert os.path.exists(doc_folder)


def test_create_document_illegal_path(tmp_config: TemporaryConfiguration) -> None:
    """POST .../documents safely falls back for paths attempting escape."""
    from papis.server.app import app

    client = TestClient(app)

    escape_paths = [
        "../outside-library",
        "../../etc/passwd",
        "subfolder/../../outside",
        "/absolute/path",
    ]

    for path in escape_paths:
        response = client.post(
            "/api/v1/libraries/test/documents",
            data={"data": json.dumps({"title": "Escape Path Test"}), "folder": path},
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "path_escape"


def test_create_document_malformed_json(tmp_config: TemporaryConfiguration) -> None:
    """POST .../documents returns 400 for malformed JSON in 'data' field."""
    from papis.server.app import app

    client = TestClient(app)

    response = client.post(
        "/api/v1/libraries/test/documents",
        data={"data": "not valid json {{{{{", "folder": "test-json"},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == "invalid_json"
    assert "error" in detail["context"]


def test_create_document_library_not_found(tmp_config: TemporaryConfiguration) -> None:
    """POST .../documents returns 404 for non-existent library."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/libraries/nonexistent/documents",
        data={"data": json.dumps({"title": "Test"}), "folder": "test"},
    )

    assert response.status_code == 404


def test_create_document_path_normalization(tmp_config: TemporaryConfiguration) -> None:
    """POST .../documents paths with special characters are normalized."""
    from papis.server.app import app

    client = TestClient(app)

    create_response = client.post(
        "/api/v1/libraries/test/documents",
        data={
            "data": json.dumps({"title": "Special Chars Test"}),
            "folder": "test!!folder<>with/special*chars",
        },
    )
    assert create_response.status_code == 201
    papis_id = create_response.json()["document"]["papis_id"]

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    assert get_response.json()["folder"] == "test-folder-with/special-chars"


def test_create_document_unique_path_suffix(tmp_config: TemporaryConfiguration) -> None:
    """POST .../documents creates unique folder names with suffix."""
    from papis.server.app import app

    client = TestClient(app)

    response1 = client.post(
        "/api/v1/libraries/test/documents",
        data={"data": json.dumps({"title": "First Doc"}), "folder": "test-path"},
    )
    assert response1.status_code == 201
    path1 = response1.json()["folder"]

    response2 = client.post(
        "/api/v1/libraries/test/documents",
        data={"data": json.dumps({"title": "Second Doc"}), "folder": "test-path"},
    )
    assert response2.status_code == 201
    path2 = response2.json()["folder"]

    assert path1 == "test-path"
    assert path2 == "test-path-a"


def test_create_document_empty_folder(tmp_config: TemporaryConfiguration) -> None:
    """POST .../documents falls back to default when folder is empty."""
    from papis.server.app import app

    client = TestClient(app)

    response = client.post(
        "/api/v1/libraries/test/documents",
        data={
            "data": json.dumps({"title": "Empty Folder Test"}),
            "folder": "",
        },
    )
    assert response.status_code == 201
    data = response.json()
    papis_id = data["document"]["papis_id"]

    assert data["folder"] == papis_id


def test_create_document_rejects_files_and_notes(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST .../documents rejects requests with files or notes fields."""
    from papis.server.app import app

    client = TestClient(app)

    response = client.post(
        "/api/v1/libraries/test/documents",
        data={
            "data": json.dumps({"title": "Test", "files": ["file.pdf"]}),
            "folder": "test",
        },
    )
    assert response.status_code == 400

    response = client.post(
        "/api/v1/libraries/test/documents",
        data={
            "data": json.dumps({"title": "Test", "notes": "some notes"}),
            "folder": "test",
        },
    )
    assert response.status_code == 400


def test_create_document_respects_per_library_config(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST .../documents uses per-library config, not global defaults."""
    import papis.config
    from papis.server.app import app

    client = TestClient(app)

    # Create a second library directory
    lib2_name = "test2"
    lib2_dir = os.path.join(tmp_config.tmpdir, "lib2")
    os.makedirs(lib2_dir)

    # Register the second library in the in-memory configuration
    cfg = papis.config.get_configuration()
    cfg[lib2_name] = {
        "dir": papis.config.escape_interp(lib2_dir),
        "add-folder-name": "{doc[title]}",
    }

    # Second library: custom folder naming via add-folder-name
    r2 = client.post(
        f"/api/v1/libraries/{lib2_name}/documents",
        data={"data": json.dumps({"title": "Second Library Doc"})},
    )
    assert r2.status_code == 201
    doc_id = r2.json()["document"]["papis_id"]

    get_response = client.get(f"/api/v1/libraries/{lib2_name}/documents/{doc_id}")
    assert "second-library-doc" in get_response.json()["folder"]


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
    assert data["document"]["title"] == "Get Test"
    assert data["document"]["papis_id"] == papis_id
    assert isinstance(data["folder"], str)


def test_get_document_not_found(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents/{id} returns 404 for non-existent document."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries/test/documents/nonexistent-id")

    assert response.status_code == 404


def test_standard_response_no_papis_local_folder_in_local_mode(
    tmp_config: TemporaryConfiguration,
) -> None:
    """Standard responses never include _papis_local_folder, even in local mode."""

    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(
        client, path="local-standard", title="Local Standard"
    )

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")

    assert response.status_code == 200
    assert "_papis_local_folder" not in response.json()["document"]


def test_create_document_with_link_files(tmp_config: TemporaryConfiguration) -> None:
    """POST /documents with link_files creates symlinks during document creation."""
    import json
    import tempfile

    from papis.server.app import app

    client = TestClient(app)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".pdf", delete=False, encoding="utf-8"
    ) as f:
        f.write("symlinked file content")
        src_path = f.name

    try:
        response = client.post(
            "/api/v1/libraries/test/documents",
            data={
                "data": json.dumps({"title": "Symlink Doc"}),
                "folder": "symlink-doc",
                "link_files": [src_path],
            },
        )

        assert response.status_code == 201
        result = response.json()
        doc_folder = result["folder"]

        assert len(result["document"].get("files", [])) == 1
        filename = result["document"]["files"][0]

        file_on_disk = os.path.join(tmp_config.libdir, doc_folder, filename)
        assert os.path.islink(file_on_disk)
        assert os.path.samefile(os.readlink(file_on_disk), src_path)

        get_response = client.get(
            f"/api/v1/libraries/test/documents/{result['document']['papis_id']}"
        )
        assert get_response.status_code == 200
        get_doc = get_response.json()["document"]
        assert filename in get_doc.get("files", [])
    finally:
        os.unlink(src_path)


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
        json={"data": {"title": "Updated Title"}},
    )

    assert response.status_code == 200
    data = response.json()["document"]
    assert data["title"] == "Updated Title"

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    get_data = get_response.json()["document"]
    assert get_data["title"] == "Updated Title"
    assert "folder" in get_response.json()

    # Verify on disk
    doc_folder = os.path.join(tmp_config.libdir, get_response.json()["folder"])
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
        json={"data": {"author": "Author To Delete"}},
    )
    assert response.status_code == 200

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"data": {"author": None}},
    )

    assert response.status_code == 200

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    get_data = get_response.json()["document"]
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
        json={"data": {"author": "New Author", "year": 2024}},
    )

    assert response.status_code == 200
    data = response.json()["document"]
    assert data["author"] == "New Author"
    assert data["year"] == 2024


def test_update_document_not_found(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../documents/{id} returns 404 for non-existent document."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.patch(
        "/api/v1/libraries/test/documents/nonexistent-id",
        json={"data": {"title": "New Title"}},
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
        json={"data": {"files": ["file.pdf"]}},
    )
    assert response.status_code == 400

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"data": {"notes": "some notes"}},
    )
    assert response.status_code == 400


def test_update_document_rejects_papis_id(
    tmp_config: TemporaryConfiguration,
) -> None:
    """PATCH .../documents/{id} rejects requests that modify papis_id."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(
        client, path="reject-papis-id", title="Reject PapisID"
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"data": {"papis_id": "new-id"}},
    )
    assert response.status_code == 400


def test_update_document_missing_folder(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../documents/{id} returns 404 when document folder is missing."""
    import shutil

    from papis.server.app import app

    client = TestClient(app)
    papis_id, path = create_test_document(
        client, path="update-missing-test", title="Update Missing Folder"
    )

    doc_dir = os.path.join(tmp_config.libdir, path)
    shutil.rmtree(doc_dir)

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"data": {"title": "New Title"}},
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "document_not_found"


# =============================================================================
# DELETE /libraries/{library}/documents/{id}
# =============================================================================


def test_delete_document(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../documents/{id} deletes document folder from disk."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="delete-test", title="Delete Test")

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    assert get_response.status_code == 200
    doc_folder = os.path.join(tmp_config.libdir, get_response.json()["folder"])
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


def test_delete_document_missing_folder(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../documents/{id} returns 404 when folder is gone."""
    import shutil

    from papis.server.app import app

    client = TestClient(app)
    papis_id, path = create_test_document(
        client, path="delete-missing-test", title="Delete Missing Folder"
    )

    doc_dir = os.path.join(tmp_config.libdir, path)
    shutil.rmtree(doc_dir)

    response = client.delete(f"/api/v1/libraries/test/documents/{papis_id}")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "document_not_found"


# =============================================================================
# Document folder operations
# =============================================================================


def test_get_document_folder(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents/{id} returns the document folder in the response."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="path-test", title="Path Test")

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")

    assert response.status_code == 200
    data = response.json()["folder"]
    assert isinstance(data, str)
    assert "path-test" in data


def test_get_document_path_not_found(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents/{id} returns 404 for non-existent document."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries/test/documents/nonexistent-id")

    assert response.status_code == 404


def test_move_document(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../documents/{id} moves document to new location via folder."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="original-path", title="Move Test")

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"folder": "new-location/moved-doc"},
    )

    assert response.status_code == 200
    data = response.json()["folder"]
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
    """PATCH .../documents/{id} returns 404 for non-existent document."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.patch(
        "/api/v1/libraries/test/documents/nonexistent-id",
        json={"folder": "new-path"},
    )

    assert response.status_code == 404


def test_move_document_path_normalization(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../documents/{id} normalizes special chars to safe folder names."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(
        client, path="original-path", title="Move Normalize Test"
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"folder": "new!!path<>with/special*chars"},
    )
    assert response.status_code == 200

    assert response.json()["folder"] == "new-path-with/special-chars"


def test_move_document_unique_path_suffix(tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../documents/{id} adds suffix when clashes arise."""
    from papis.server.app import app

    client = TestClient(app)

    create_test_document(client, path="target-path", title="First")
    papis_id2, _ = create_test_document(client, path="other-path", title="Second")

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id2}",
        json={"folder": "target-path"},
    )
    assert response.status_code == 200

    path = response.json()["folder"]
    assert path == "target-path-a"


def test_move_document_format_pattern(
    tmp_config: TemporaryConfiguration,
) -> None:
    """PATCH .../documents/{id} supports format patterns for folder."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(
        client, path="old-path", title="My Great Paper", author="Smith"
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"folder": "{doc[author]}/{doc[title]}"},
    )
    assert response.status_code == 200
    assert response.json()["folder"] == "smith/my-great-paper"

    # Verify on disk
    doc_folder = os.path.join(tmp_config.libdir, "smith", "my-great-paper")
    assert os.path.exists(doc_folder)
    assert not os.path.exists(os.path.join(tmp_config.libdir, "old-path"))


def test_move_document_default_folder(
    tmp_config: TemporaryConfiguration,
) -> None:
    """PATCH .../documents/{id} uses add-folder-name when folder is null."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(
        client, path="old-path", title="Default Folder Doc"
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"folder": None},
    )
    assert response.status_code == 200

    path = response.json()["folder"]
    assert papis_id in path

    # Verify on disk
    assert not os.path.exists(os.path.join(tmp_config.libdir, "old-path"))
    assert os.path.exists(os.path.join(tmp_config.libdir, path))


def test_move_document_path_escape(
    tmp_config: TemporaryConfiguration,
) -> None:
    """PATCH .../documents/{id} rejects folder paths attempting escape."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="old-path", title="Escape Test")

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"folder": "../outside-library"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "path_escape"
