from __future__ import annotations

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
# GET /api/v1/exporters
# =============================================================================


def test_list_exporters(tmp_config: TemporaryConfiguration) -> None:
    """GET /exporters returns a list of available export formats."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/exporters")
    assert response.status_code == 200

    data = {e["name"]: e["content_type"] for e in response.json()}
    assert data["json"] == "application/json"
    assert data["bibtex"] == "text/x-bibtex"


# =============================================================================
# GET /api/v1/libraries/{library}/documents/{id}
# =============================================================================


def test_get_document_default_json(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents/{id} returns JSON by default."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(
        client, path="default-test", title="Default JSON"
    )

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


# =============================================================================
# GET /api/v1/libraries/{library}/documents/{id}?format=...
# =============================================================================


def test_export_document_bibtex(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents/{id}?format=bibtex returns bibtex string."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="bibtex-test", title="Test BibTeX")

    response = client.get(
        f"/api/v1/libraries/test/documents/{papis_id}", params={"format": "bibtex"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/x-bibtex; charset=utf-8"
    assert "Test BibTeX" in response.text


def test_export_document_json(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents/{id}?format=json returns JSON."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="json-test", title="Test JSON")

    response = client.get(
        f"/api/v1/libraries/test/documents/{papis_id}", params={"format": "json"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    data = response.json()
    assert isinstance(data, dict)
    assert data["title"] == "Test JSON"


def test_export_document_unknown_format(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents/{id}?format=unknown returns 400 with valid formats."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="unknown-test", title="Unknown")

    response = client.get(
        f"/api/v1/libraries/test/documents/{papis_id}", params={"format": "unknown"}
    )

    assert response.status_code == 400
    assert "unknown" in response.json()["detail"]
    assert "json" in response.json()["detail"]


# =============================================================================
# GET /api/v1/libraries/{library}/documents
# =============================================================================


def test_export_documents_default_json(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents returns JSON by default."""
    from papis.server.app import app

    client = TestClient(app)
    create_test_document(client, path="multi-json-1", title="Multi JSON 1")
    create_test_document(client, path="multi-json-2", title="Multi JSON 2")

    response = client.get("/api/v1/libraries/test/documents")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"


# =============================================================================
# GET /api/v1/libraries/{library}/documents?format=...
# =============================================================================


def test_export_documents_bibtex(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents?format=bibtex returns bibtex for all documents."""
    from papis.server.app import app

    client = TestClient(app)
    create_test_document(client, path="multi-test-1", title="Multi Doc 1")
    create_test_document(client, path="multi-test-2", title="Multi Doc 2")

    response = client.get(
        "/api/v1/libraries/test/documents", params={"format": "bibtex"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/x-bibtex; charset=utf-8"
    assert "Multi Doc 1" in response.text
    assert "Multi Doc 2" in response.text


def test_export_documents_with_query(tmp_config: TemporaryConfiguration) -> None:
    """GET .../documents?q=...&format=bibtex exports only matching documents."""
    from papis.server.app import app

    client = TestClient(app)
    create_test_document(client, path="query-export-1", title="Export Me")
    create_test_document(client, path="query-export-2", title="Not Me")

    response = client.get(
        "/api/v1/libraries/test/documents",
        params={"q": "title:'Export Me'", "format": "bibtex"},
    )

    assert response.status_code == 200
    assert "Export Me" in response.text
    assert "Not Me" not in response.text
