from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from papis.testing import TemporaryConfiguration

from tests.server.conftest import create_test_document

# =============================================================================
# GET /api/v1/libraries/{library}/export
# =============================================================================


def test_list_export_formats(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET /export returns a list of available export formats."""

    response = client.get("/api/v1/libraries/test/export")
    assert response.status_code == 200

    data = {e["name"]: e["content_type"] for e in response.json()["exporters"]}
    assert data["json"] == "application/json"
    assert data["bibtex"] == "text/x-bibtex"


# =============================================================================
# POST /api/v1/libraries/{library}/export
# =============================================================================


def test_export_document_bibtex(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST /export?format=bibtex returns bibtex string."""

    papis_id, _ = create_test_document(client, path="bibtex-test", title="Test BibTeX")

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    doc_data = get_response.json()["metadata"]

    response = client.post(
        "/api/v1/libraries/test/export",
        json={"documents": [doc_data]},
        params={"format": "bibtex"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/x-bibtex; charset=utf-8"
    assert "Test BibTeX" in response.text


def test_export_document_json(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST /export?format=json returns JSON list."""

    papis_id, _ = create_test_document(client, path="json-test", title="Test JSON")

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    doc_data = get_response.json()["metadata"]

    response = client.post(
        "/api/v1/libraries/test/export",
        json={"documents": [doc_data]},
        params={"format": "json"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    data = response.json()
    # The json exporter always returns a list, even for a single document
    assert isinstance(data, list)
    assert data[0]["title"] == "Test JSON"


def test_export_document_unknown_format(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST /export?format=unknown returns 400 with valid formats."""

    papis_id, _ = create_test_document(client, path="unknown-test", title="Unknown")

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    doc_data = get_response.json()["metadata"]

    response = client.post(
        "/api/v1/libraries/test/export",
        json={"documents": [doc_data]},
        params={"format": "unknown"},
    )

    assert response.status_code == 400
    assert response.json()["type"] == "/errors/unknown-export-format"


def test_export_documents_bibtex(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST /export?format=bibtex exports all provided documents."""

    create_test_document(client, path="multi-test-1", title="Multi Doc 1")
    create_test_document(client, path="multi-test-2", title="Multi Doc 2")

    list_response = client.get("/api/v1/libraries/test/documents")
    docs_data = [item["metadata"] for item in list_response.json()["documents"]]

    response = client.post(
        "/api/v1/libraries/test/export",
        json={"documents": docs_data},
        params={"format": "bibtex"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/x-bibtex; charset=utf-8"
    assert "Multi Doc 1" in response.text
    assert "Multi Doc 2" in response.text


def test_json_export_includes_papis_local_folder_in_local_mode(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """Export includes _papis_local_folder in local mode (the default)."""

    papis_id, _ = create_test_document(client, path="local-json", title="Local JSON")

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    doc_data = get_response.json()["metadata"]

    response = client.post(
        "/api/v1/libraries/test/export?format=json",
        json={"documents": [doc_data]},
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "_papis_local_folder" in data[0]


def test_json_export_no_papis_local_folder_remote(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """Export does not include _papis_local_folder in non-local mode."""
    import papis.config

    papis.config.set("server-local-mode", False)

    papis_id, _ = create_test_document(client, path="remote-json", title="Remote JSON")

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    doc_data = get_response.json()["metadata"]

    response = client.post(
        "/api/v1/libraries/test/export?format=json",
        json={"documents": [doc_data]},
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "_papis_local_folder" not in data[0]
