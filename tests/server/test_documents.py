from __future__ import annotations

import json
import os
import shutil
import tempfile
from io import BytesIO
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

import papis.config
import papis.document
from papis.server.app import app

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from papis.server.events import EventBroker
    from papis.testing import TemporaryConfiguration

from tests.server.conftest import create_test_document, populate_docs

# =============================================================================
# GET /libraries/{library}/documents
# =============================================================================


def test_get_documents_empty(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../documents returns empty list when library has no documents."""

    response = client.get("/api/v1/libraries/test/documents")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["documents"], list)
    assert len(data["documents"]) == 0


def test_get_documents_with_query(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../documents with query returns only matching documents."""

    create_test_document(client, path="query-test-1", title="Find this doc")
    create_test_document(client, path="query-test-2", title="Not this doc")

    response = client.get("/api/v1/libraries/test/documents", params={"q": "Find"})

    assert response.status_code == 200
    data = response.json()
    docs = data["documents"]
    assert len(docs) == 1
    assert docs[0]["metadata"]["title"] == "Find this doc"


def test_get_documents_empty_query_matches_all(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET .../documents with an omitted or empty q returns all documents."""

    create_test_document(client, path="empty-q-1", title="First doc")
    create_test_document(client, path="empty-q-2", title="Second doc")

    resp = client.get("/api/v1/libraries/test/documents")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2

    resp = client.get("/api/v1/libraries/test/documents", params={"q": ""})
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_get_documents_metadata_omits_unset_fields(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """Response metadata only contains fields actually set on the document."""

    papis_id, _ = create_test_document(client, path="meta-shape", title="Only title")

    resp = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    assert resp.status_code == 200
    metadata = resp.json()["metadata"]
    assert metadata["title"] == "Only title"
    assert "year" not in metadata
    assert "author" not in metadata
    assert "tags" not in metadata


def test_get_documents_with_id(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../documents with id returns only the matching document."""

    id1, _ = create_test_document(client, path="id-test-1", title="First doc")
    create_test_document(client, path="id-test-2", title="Second doc")

    response = client.get("/api/v1/libraries/test/documents", params={"id": id1})

    assert response.status_code == 200
    data = response.json()
    docs = data["documents"]
    assert len(docs) == 1
    assert docs[0]["metadata"]["papis_id"] == id1
    assert docs[0]["metadata"]["title"] == "First doc"


def test_get_documents_id_folder_query_combined(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET .../documents id + folder + q combine with AND semantics through the API."""

    create_test_document(client, path="combo/alpha", title="Combo Alpha Unique")
    create_test_document(client, path="combo/beta", title="Combo Beta Unique")
    create_test_document(client, path="other/gamma", title="Combo Gamma Unique")

    resp = client.get(
        "/api/v1/libraries/test/documents",
        params={"q": "Unique", "folder": "combo"},
    )
    assert resp.status_code == 200
    combo_ids = {d["metadata"]["papis_id"] for d in resp.json()["documents"]}
    assert len(combo_ids) == 2

    target_id = next(iter(combo_ids))
    resp = client.get(
        "/api/v1/libraries/test/documents",
        params={"q": "Unique", "folder": "combo", "id": target_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["documents"][0]["metadata"]["papis_id"] == target_id


def test_get_documents_library_not_found(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../documents returns 404 for non-existent library."""

    response = client.get("/api/v1/libraries/nonexistent/documents")

    assert response.status_code == 404


def test_get_document_folder_not_found(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../documents returns 404 when folder is missing."""
    papis_id, doc_path = create_test_document(client, path="test-doc")

    doc_folder = os.path.join(tmp_config.libdir, doc_path)
    shutil.rmtree(doc_folder)

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    assert response.status_code == 404


def test_pagination_limit_zero(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../documents with limit=0 returns an empty page."""

    populate_docs(client, 5)

    resp = client.get(
        "/api/v1/libraries/test/documents",
        params={"limit": 0, "offset": 0},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert data["documents"] == []
    assert data["limit"] == 0


def test_pagination_paged_query(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../documents with limit/offset returns the requested page."""

    populate_docs(client, 10)

    resp = client.get(
        "/api/v1/libraries/test/documents",
        params={"limit": 3, "offset": 4},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 10
    assert data["limit"] == 3
    assert data["offset"] == 4
    assert len(data["documents"]) == 3

    resp2 = client.get(
        "/api/v1/libraries/test/documents",
        params={"limit": 3, "offset": 7},
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    page1 = {d["metadata"]["papis_id"] for d in data["documents"]}
    page2 = {d["metadata"]["papis_id"] for d in data2["documents"]}
    assert len(page1) == 3
    assert len(page2) == 3
    assert not page1 & page2


def test_pagination_sort_ascending(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../documents sorted by year ascending."""

    populate_docs(client, 10)

    resp = client.get(
        "/api/v1/libraries/test/documents",
        params={"sort": "year", "limit": 50},
    )
    assert resp.status_code == 200
    years = [d["metadata"].get("year") for d in resp.json()["documents"]]
    assert years == sorted(years)


def test_pagination_sort_descending(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../documents sorted by year descending."""

    populate_docs(client, 10)

    resp = client.get(
        "/api/v1/libraries/test/documents",
        params={"sort": "year", "reverse": "true", "limit": 50},
    )
    assert resp.status_code == 200
    years = [d["metadata"].get("year") for d in resp.json()["documents"]]
    assert years == sorted(years, reverse=True)


def test_pagination_sort_missing_last(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../documents sorts documents missing the key last in both directions."""

    for i in range(5):
        create_test_document(
            client,
            path=f"no-year-{i}",
            title=f"MissingYear {i}",
        )
    for i in range(5):
        create_test_document(
            client,
            path=f"with-year-{i}",
            title=f"HasYear {i}",
            year=2000 + i,
        )

    # ascending
    resp = client.get(
        "/api/v1/libraries/test/documents",
        params={"sort": "year", "limit": 50},
    )
    assert resp.status_code == 200
    docs = resp.json()["documents"]
    has_year = [d["metadata"].get("year") is not None for d in docs]
    split = has_year.index(False)
    assert all(has_year[:split])
    assert not any(has_year[split:])

    # descending
    resp = client.get(
        "/api/v1/libraries/test/documents",
        params={"sort": "year", "reverse": "true", "limit": 50},
    )
    assert resp.status_code == 200
    docs = resp.json()["documents"]
    has_year = [d["metadata"].get("year") is not None for d in docs]
    split = has_year.index(False)
    assert all(has_year[:split])
    assert not any(has_year[split:])


def test_pagination_limit_capped(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../documents caps limit at server-max-page-size."""
    populate_docs(client, 10)

    papis.config.set("server-max-page-size", 3)

    resp = client.get(
        "/api/v1/libraries/test/documents",
        params={"limit": 100},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 10
    assert len(data["documents"]) == 3
    assert data["limit"] == 3


def test_pagination_limit_not_capped_by_default(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET .../documents does not cap limit by default."""

    populate_docs(client, 10)

    resp = client.get(
        "/api/v1/libraries/test/documents",
        params={"limit": 100},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 10
    assert len(data["documents"]) == 10
    assert data["limit"] == 100


def test_pagination_unlimited_limit_null(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET .../documents without paging params returns all documents."""

    populate_docs(client, 10)

    resp = client.get("/api/v1/libraries/test/documents")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 10
    assert len(data["documents"]) == 10
    assert data["limit"] is None


def test_pagination_since_version_response_shape(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET .../documents with `since_version` returns all changed docs."""

    populate_docs(client, 3)

    resp = client.get(
        "/api/v1/libraries/test/documents",
        params={"since_version": -1},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["documents"]) == 3
    assert data["limit"] is None
    assert data["offset"] == 0


def test_pagination_since_version_mutual_exclusion(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET .../documents rejects since_version combined with q, folder, or id."""

    resp = client.get(
        "/api/v1/libraries/test/documents",
        params={"since_version": 0, "q": "test"},
    )
    assert resp.status_code == 400
    data = resp.json()
    assert data["type"] == "/errors/mutually-exclusive"

    resp = client.get(
        "/api/v1/libraries/test/documents",
        params={"since_version": 0, "id": "deadbeef"},
    )
    assert resp.status_code == 400
    data = resp.json()
    assert data["type"] == "/errors/mutually-exclusive"


def test_pagination_since_version_filters(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET .../documents with since_version returns only newer documents."""
    broker: EventBroker = app.state.broker

    # Create first doc
    pid1, _ = create_test_document(client, path="since-first", title="First")
    v1 = broker.get_lib_version("test")

    # Create second doc (its per-doc version > v1)
    pid2, _ = create_test_document(client, path="since-second", title="Second")

    # since_version = v1 should return only pid2 (version > v1)
    response = client.get(
        "/api/v1/libraries/test/documents",
        params={"since_version": v1},
    )
    assert response.status_code == 200
    docs = response.json()["documents"]
    pids = {d["metadata"]["papis_id"] for d in docs}
    assert pid2 in pids
    assert pid1 not in pids

    # since_version = 0 should return all known docs
    # (all per-doc versions are > 0)
    response = client.get(
        "/api/v1/libraries/test/documents",
        params={"since_version": 0},
    )
    assert response.status_code == 200
    docs = response.json()["documents"]
    pids = {d["metadata"]["papis_id"] for d in docs}
    assert pid1 in pids
    assert pid2 in pids


def test_pagination_bad_limit_returns_validation_error(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET .../documents with a negative limit returns 422."""

    resp = client.get(
        "/api/v1/libraries/test/documents",
        params={"limit": -1},
    )
    assert resp.status_code == 422


def test_pagination_bad_offset_returns_validation_error(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET .../documents with a negative offset returns 422."""

    resp = client.get(
        "/api/v1/libraries/test/documents",
        params={"offset": -1},
    )
    assert resp.status_code == 422


def test_pagination_unknown_sort_field_ok(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET .../documents sorted by an unknown field returns all documents."""

    ids = set(populate_docs(client, 5))

    resp = client.get(
        "/api/v1/libraries/test/documents",
        params={"sort": "nonexistent_field", "limit": 50},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    returned_ids = {d["metadata"]["papis_id"] for d in data["documents"]}
    assert returned_ids == ids


# =============================================================================
# POST /libraries/{library}/documents
# =============================================================================


def test_create_document(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../documents creates a new document."""

    papis_id, _ = create_test_document(client, path="test-doc", title="Test Document")

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    assert response.status_code == 200
    data = response.json()["metadata"]
    assert data["title"] == "Test Document"

    # Verify on disk
    doc_folder = os.path.join(tmp_config.libdir, response.json()["folder"])
    assert os.path.exists(doc_folder)


def test_create_document_generates_ref(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../documents auto-generates a bibtex ref when not provided."""

    response = client.post(
        "/api/v1/libraries/test/documents",
        data={
            "metadata": json.dumps({"title": "Ref Test", "author": "Someone"}),
            "folder": "ref-test",
        },
    )

    assert response.status_code == 201
    data = response.json()["metadata"]
    assert "ref" in data
    assert data["ref"] != ""


@pytest.mark.parametrize("client", [{"raise_server_exceptions": False}], indirect=True)
def test_create_document_new_failure_returns_500(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST .../documents returns 500 when new() fails."""
    with patch.object(papis.document, "new", side_effect=ValueError("new failed")):
        response = client.post(
            "/api/v1/libraries/test/documents",
            data={"metadata": '{"title": "Fail Test"}', "folder": "fail-path"},
        )

    assert response.status_code == 500
    data = response.json()
    assert data["type"] == "/errors/internal-server-error"


def test_create_document_with_extra_fields(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../documents accepts fields not explicitly defined."""

    response = client.post(
        "/api/v1/libraries/test/documents",
        data={
            "metadata": json.dumps({"title": "Test", "custom_field": "custom_value"}),
            "folder": "test-extra",
        },
    )

    assert response.status_code == 201
    data = response.json()["metadata"]
    assert data["title"] == "Test"
    assert data["custom_field"] == "custom_value"


def test_create_document_in_subfolder(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../documents creates document in subfolders."""

    papis_id, _ = create_test_document(
        client, path="subfolder/nested/test", title="Subfolder Test"
    )

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    assert get_response.status_code == 200
    assert get_response.json()["folder"] == "subfolder/nested/test"

    # Verify on disk
    doc_folder = os.path.join(tmp_config.libdir, "subfolder", "nested", "test")
    assert os.path.exists(doc_folder)


def test_create_document_illegal_path(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../documents safely falls back for paths attempting escape."""

    escape_paths = [
        "../outside-library",
        "../../etc/passwd",
        "subfolder/../../outside",
        "/absolute/path",
    ]

    for path in escape_paths:
        response = client.post(
            "/api/v1/libraries/test/documents",
            data={
                "metadata": json.dumps({"title": "Escape Path Test"}),
                "folder": path,
            },
        )
        assert response.status_code == 400
        assert response.json()["type"] == "/errors/path-escape"


def test_create_document_malformed_json(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../documents returns 400 for malformed JSON in 'data' field."""

    response = client.post(
        "/api/v1/libraries/test/documents",
        data={"metadata": "not valid json {{{{{", "folder": "test-json"},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["type"] == "/errors/invalid-json"
    assert "error" in data["context"]


def test_create_document_library_not_found(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../documents returns 404 for non-existent library."""

    response = client.post(
        "/api/v1/libraries/nonexistent/documents",
        data={"metadata": json.dumps({"title": "Test"}), "folder": "test"},
    )

    assert response.status_code == 404


def test_create_document_path_normalization(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../documents paths with special characters are normalized."""

    create_response = client.post(
        "/api/v1/libraries/test/documents",
        data={
            "metadata": json.dumps({"title": "Special Chars Test"}),
            "folder": "test!!folder<>with/special*chars",
        },
    )
    assert create_response.status_code == 201
    papis_id = create_response.json()["metadata"]["papis_id"]

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    assert get_response.json()["folder"] == "test-folder-with/special-chars"


def test_create_document_unique_path_suffix(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../documents creates unique folder names with suffix."""

    response1 = client.post(
        "/api/v1/libraries/test/documents",
        data={"metadata": json.dumps({"title": "First Doc"}), "folder": "test-path"},
    )
    assert response1.status_code == 201
    path1 = response1.json()["folder"]

    response2 = client.post(
        "/api/v1/libraries/test/documents",
        data={"metadata": json.dumps({"title": "Second Doc"}), "folder": "test-path"},
    )
    assert response2.status_code == 201
    path2 = response2.json()["folder"]

    assert path1 == "test-path"
    assert path2 == "test-path-a"


def test_create_document_empty_folder(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../documents falls back to default when folder is empty."""

    response = client.post(
        "/api/v1/libraries/test/documents",
        data={
            "metadata": json.dumps({"title": "Empty Folder Test"}),
            "folder": "",
        },
    )
    assert response.status_code == 201
    data = response.json()
    papis_id = data["metadata"]["papis_id"]

    assert data["folder"] == papis_id


def test_create_document_rejects_immutable_field_changes(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST .../documents rejects setting immutable fields (files, notes, papis_id)."""

    r_files = client.post(
        "/api/v1/libraries/test/documents",
        data={
            "metadata": json.dumps({"title": "Test", "files": ["file.pdf"]}),
            "folder": "test",
        },
    )
    r_notes = client.post(
        "/api/v1/libraries/test/documents",
        data={
            "metadata": json.dumps({"title": "Test", "notes": "some notes"}),
            "folder": "test",
        },
    )
    r_papis_id = client.post(
        "/api/v1/libraries/test/documents",
        data={
            "metadata": json.dumps({"title": "Test", "papis_id": "custom-id"}),
            "folder": "test",
        },
    )

    assert r_files.status_code == 400
    assert r_notes.status_code == 400
    assert r_papis_id.status_code == 400


def test_create_document_allows_immutable_fields_when_null(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST .../documents accepts immutable fields set to null (no change)."""

    response = client.post(
        "/api/v1/libraries/test/documents",
        data={
            "metadata": json.dumps({
                "title": "Test",
                "files": None,
                "notes": None,
                "papis_id": None,
            }),
            "folder": "test",
        },
    )
    assert response.status_code == 201
    data = response.json()["metadata"]
    assert data["papis_id"] is not None


def test_create_document_respects_per_library_config(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST .../documents uses per-library config, not global defaults."""
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
        data={"metadata": json.dumps({"title": "Second Library Doc"})},
    )
    assert r2.status_code == 201
    doc_id = r2.json()["metadata"]["papis_id"]

    get_response = client.get(f"/api/v1/libraries/{lib2_name}/documents/{doc_id}")
    assert "second-library-doc" in get_response.json()["folder"]


# =============================================================================
# GET /libraries/{library}/documents/{id}
# =============================================================================


def test_get_document(client: TestClient, tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents/{id} returns a specific document by ID."""

    papis_id, _ = create_test_document(client, path="get-test", title="Get Test")

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["title"] == "Get Test"
    assert data["metadata"]["papis_id"] == papis_id
    assert isinstance(data["folder"], str)


def test_get_document_not_found(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../documents/{id} returns 404 for non-existent document."""

    response = client.get("/api/v1/libraries/test/documents/nonexistent-id")

    assert response.status_code == 404


def test_standard_response_no_papis_local_folder_in_local_mode(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """Standard responses never include _papis_local_folder, even in local mode."""

    papis_id, _ = create_test_document(
        client, path="local-standard", title="Local Standard"
    )

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")

    assert response.status_code == 200
    assert "_papis_local_folder" not in response.json()["metadata"]


def test_create_document_with_link_files(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST /documents with link_files creates symlinks during document creation."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".pdf", delete=False, encoding="utf-8"
    ) as f:
        f.write("symlinked file content")
        src_path = f.name

    try:
        response = client.post(
            "/api/v1/libraries/test/documents",
            data={
                "metadata": json.dumps({"title": "Symlink Doc"}),
                "folder": "symlink-doc",
                "link_files": [src_path],
            },
        )

        assert response.status_code == 201
        result = response.json()
        doc_folder = result["folder"]

        assert len(result["metadata"].get("files", [])) == 1
        filename = result["metadata"]["files"][0]

        file_on_disk = os.path.join(tmp_config.libdir, doc_folder, filename)
        assert os.path.islink(file_on_disk)
        assert os.path.samefile(os.readlink(file_on_disk), src_path)

        get_response = client.get(
            f"/api/v1/libraries/test/documents/{result['metadata']['papis_id']}"
        )
        assert get_response.status_code == 200
        get_doc = get_response.json()["metadata"]
        assert filename in get_doc.get("files", [])
    finally:
        os.unlink(src_path)


# =============================================================================
# PATCH /libraries/{library}/documents/{id}
# =============================================================================


def test_update_document(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """PATCH .../documents/{id} updates document metadata."""
    papis_id, _ = create_test_document(
        client, path="update-test", title="Original Title"
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"metadata": {"title": "Updated Title"}},
    )

    assert response.status_code == 200
    data = response.json()["metadata"]
    assert data["title"] == "Updated Title"

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    get_data = get_response.json()["metadata"]
    assert get_data["title"] == "Updated Title"
    assert "folder" in get_response.json()

    # Verify on disk
    doc_folder = os.path.join(tmp_config.libdir, get_response.json()["folder"])
    doc_on_disk = papis.document.Document(folder=doc_folder)
    assert doc_on_disk["title"] == "Updated Title"


def test_update_document_delete_field(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """PATCH .../documents/{id} can delete a field."""

    papis_id, _ = create_test_document(
        client, path="delete-field-test", title="Delete Field Test"
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"metadata": {"author": "Author To Delete"}},
    )
    assert response.status_code == 200

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"metadata": {"author": None}},
    )

    assert response.status_code == 200

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    get_data = get_response.json()["metadata"]
    assert "author" not in get_data


def test_update_document_add_field(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """PATCH .../documents/{id} can add new fields."""

    papis_id, _ = create_test_document(
        client, path="add-field-test", title="Add Field Test"
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"metadata": {"author": "New Author", "year": 2024}},
    )

    assert response.status_code == 200
    data = response.json()["metadata"]
    assert data["author"] == "New Author"
    assert data["year"] == 2024


def test_update_document_not_found(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """PATCH .../documents/{id} returns 404 for non-existent document."""

    response = client.patch(
        "/api/v1/libraries/test/documents/nonexistent-id",
        json={"metadata": {"title": "New Title"}},
    )

    assert response.status_code == 404


def test_update_document_noop(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """PATCH .../documents/{id} with neither data nor folder is a no-op."""

    papis_id, _ = create_test_document(client, path="noop-test", title="Noop Test")

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["title"] == "Noop Test"


def test_update_document_rejects_immutable_field_changes(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """PATCH .../documents/{id} rejects changing immutable fields to new values."""

    papis_id, _ = create_test_document(client, path="reject-test", title="Reject Test")

    r_files = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"metadata": {"files": ["file.pdf"]}},
    )
    r_notes = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"metadata": {"notes": "some notes"}},
    )
    r_papis_id = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"metadata": {"papis_id": "new-id"}},
    )

    assert r_files.status_code == 400
    assert r_notes.status_code == 400
    assert r_papis_id.status_code == 400


def test_update_document_allows_immutable_fields_when_unchanged(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """PATCH .../documents/{id} accepts immutable fields when value unchanged."""
    create_resp = client.post(
        "/api/v1/libraries/test/documents",
        data={
            "metadata": json.dumps({"title": "Unchanged Test"}),
            "folder": "unchanged-test",
        },
        files={
            "files": ("paper.pdf", BytesIO(b"content"), "application/pdf"),
        },
    )
    assert create_resp.status_code == 201
    papis_id = create_resp.json()["metadata"]["papis_id"]
    notes_resp = client.post(f"/api/v1/libraries/test/documents/{papis_id}/notes")
    assert notes_resp.status_code == 201

    doc_resp = client.get(f"/api/v1/libraries/test/documents/{papis_id}").json()
    metadata = doc_resp["metadata"]

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"metadata": metadata},
    )
    assert response.status_code == 200


def test_update_document_missing_folder(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """PATCH .../documents/{id} returns 404 when document folder is missing."""
    import shutil

    papis_id, doc_path = create_test_document(
        client, path="update-missing-test", title="Update Missing Folder"
    )

    doc_dir = os.path.join(tmp_config.libdir, doc_path)
    shutil.rmtree(doc_dir)

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"metadata": {"title": "New Title"}},
    )

    assert response.status_code == 404
    assert response.json()["type"] == "/errors/document-not-found"


# =============================================================================
# DELETE /libraries/{library}/documents/{id}
# =============================================================================


def test_delete_document(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """DELETE .../documents/{id} deletes document folder from disk."""

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


def test_delete_document_not_found(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """DELETE .../documents/{id} returns 404 for non-existent document."""

    response = client.delete("/api/v1/libraries/test/documents/nonexistent-id")

    assert response.status_code == 404


def test_delete_document_missing_folder(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """DELETE .../documents/{id} returns 404 when folder is gone."""
    papis_id, doc_path = create_test_document(
        client, path="delete-missing-test", title="Delete Missing Folder"
    )

    doc_dir = os.path.join(tmp_config.libdir, doc_path)
    shutil.rmtree(doc_dir)

    response = client.delete(f"/api/v1/libraries/test/documents/{papis_id}")

    assert response.status_code == 404
    assert response.json()["type"] == "/errors/document-not-found"


# =============================================================================
# Document folder operations
# =============================================================================


def test_get_document_folder(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../documents/{id} returns the document folder in the response."""

    papis_id, _ = create_test_document(client, path="path-test", title="Path Test")

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")

    assert response.status_code == 200
    data = response.json()["folder"]
    assert isinstance(data, str)
    assert "path-test" in data


def test_get_document_path_not_found(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../documents/{id} returns 404 for non-existent document."""

    response = client.get("/api/v1/libraries/test/documents/nonexistent-id")

    assert response.status_code == 404


def test_move_document(client: TestClient, tmp_config: TemporaryConfiguration) -> None:
    """PATCH .../documents/{id} moves document to new location via folder."""

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


def test_move_document_not_found(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """PATCH .../documents/{id} returns 404 for non-existent document."""

    response = client.patch(
        "/api/v1/libraries/test/documents/nonexistent-id",
        json={"folder": "new-path"},
    )

    assert response.status_code == 404


def test_move_document_path_normalization(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """PATCH .../documents/{id} normalizes special chars to safe folder names."""

    papis_id, _ = create_test_document(
        client, path="original-path", title="Move Normalize Test"
    )

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"folder": "new!!path<>with/special*chars"},
    )
    assert response.status_code == 200

    assert response.json()["folder"] == "new-path-with/special-chars"


def test_move_document_unique_path_suffix(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """PATCH .../documents/{id} returns 409 when target folder is occupied."""

    create_test_document(client, path="target-path", title="First")
    papis_id2, _ = create_test_document(client, path="other-path", title="Second")

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id2}",
        json={"folder": "target-path"},
    )
    assert response.status_code == 409
    error = response.json()
    assert error["type"] == "/errors/folder-exists"


def test_move_document_format_pattern(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """PATCH .../documents/{id} supports format patterns for folder."""

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
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """PATCH .../documents/{id} uses add-folder-name when folder is null."""

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
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """PATCH .../documents/{id} rejects folder paths attempting escape."""

    papis_id, _ = create_test_document(client, path="old-path", title="Escape Test")

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"folder": "../outside-library"},
    )

    assert response.status_code == 400
    assert response.json()["type"] == "/errors/path-escape"


# =============================================================================
# Versioning tests (ETag, If-Match, If-None-Match)
# =============================================================================


def test_etag_on_create_response(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../documents returns an ETag header with the document version."""

    response = client.post(
        "/api/v1/libraries/test/documents",
        data={
            "metadata": json.dumps({"title": "ETag Test"}),
            "folder": "etag-test",
        },
    )
    assert response.status_code == 201
    etag = response.headers.get("ETag")
    assert etag is not None
    assert etag.startswith('"')
    assert etag.endswith('"')
    version = int(etag.strip('"'))
    assert version >= 1


def test_etag_on_update_response(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """PATCH .../documents/{id} returns an ETag header."""

    papis_id, _ = create_test_document(client, path="etag-update", title="ETag Update")

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"metadata": {"title": "Updated for ETag"}},
    )
    assert response.status_code == 200
    etag = response.headers.get("ETag")
    assert etag is not None
    version = int(etag.strip('"'))
    assert version >= 2


def test_if_match_mismatch_returns_412(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """PATCH .../documents/{id} with non-matching If-Match returns 412."""

    papis_id, _ = create_test_document(
        client, path="if-match-fail", title="If-Match Fail"
    )

    # PATCH with a wrong ETag
    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"metadata": {"title": "Should Not Update"}},
        headers={"If-Match": '"999"'},
    )
    assert response.status_code == 412
    data = response.json()
    assert data["type"] == "/errors/version-mismatch"
    assert data["context"]["expected_version"] == 999
    assert data["context"]["current_version"] >= 0
    assert data["context"]["id"] == papis_id

    # Verify document was not updated
    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    assert get_response.json()["metadata"]["title"] == "If-Match Fail"


def test_if_match_match_allows_mutation(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """PATCH .../documents/{id} with matching If-Match proceeds normally."""

    papis_id, _ = create_test_document(
        client, path="if-match-pass", title="If-Match Pass"
    )

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    etag = get_response.headers.get("ETag")
    assert etag is not None

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"metadata": {"title": "Updated Successfully"}},
        headers={"If-Match": etag},
    )
    assert response.status_code == 200
    assert response.json()["metadata"]["title"] == "Updated Successfully"


def test_if_none_match_match_returns_304(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../documents/{id} with matching If-None-Match returns 304."""

    papis_id, _ = create_test_document(client, path="304-match", title="304 Match")

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    etag = get_response.headers.get("ETag")
    assert etag is not None

    response = client.get(
        f"/api/v1/libraries/test/documents/{papis_id}",
        headers={"If-None-Match": etag},
    )
    assert response.status_code == 304
    assert response.content == b""


def test_if_none_match_mismatch_returns_200(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../documents/{id} with non-matching If-None-Match returns 200."""

    papis_id, _ = create_test_document(
        client, path="200-mismatch", title="200 Mismatch"
    )

    response = client.get(
        f"/api/v1/libraries/test/documents/{papis_id}",
        headers={"If-None-Match": '"999"'},
    )
    assert response.status_code == 200
    doc = response.json()["metadata"]
    assert doc["papis_id"] == papis_id
    assert doc["title"] == "200 Mismatch"


def test_get_documents_if_none_match_returns_304(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET .../documents with matching If-None-Match returns 304."""

    create_test_document(client, path="304-list-match-a", title="304 List A")
    create_test_document(client, path="304-list-match-b", title="304 List B")

    get_response = client.get("/api/v1/libraries/test/documents")
    etag = get_response.headers.get("ETag")
    assert etag is not None

    response = client.get(
        "/api/v1/libraries/test/documents",
        headers={"If-None-Match": etag},
    )
    assert response.status_code == 304
    assert response.content == b""


def test_get_documents_if_none_match_mismatch_returns_200(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET .../documents with non-matching If-None-Match returns 200."""

    create_test_document(client, path="200-list-mismatch-a", title="200 Mismatch A")
    create_test_document(client, path="200-list-mismatch-b", title="200 Mismatch B")

    response = client.get(
        "/api/v1/libraries/test/documents",
        headers={"If-None-Match": '"999"'},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 2
