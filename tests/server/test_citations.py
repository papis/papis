from __future__ import annotations

import os
from typing import TYPE_CHECKING
from unittest.mock import patch

import yaml

import papis.crossref

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from papis.testing import TemporaryConfiguration

from tests.server.conftest import create_test_document

# =============================================================================
# GET /libraries/{library}/documents/{id}/citations
# =============================================================================


def test_get_citations_empty(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../citations returns [] when no citations file exists."""

    papis_id, _ = create_test_document(client)

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/citations")
    assert response.status_code == 200
    assert response.json() == {"citations": []}


def test_get_citations_with_data(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../citations returns data when citations file exists."""

    papis_id, doc_path = create_test_document(client)

    citations_data: list[dict[str, str]] = [
        {"title": "Referenced Work", "doi": "10.1234/cited", "author": "Some Author"}
    ]

    citations_file = os.path.join(tmp_config.libdir, doc_path, "citations.yaml")
    with open(citations_file, "w", encoding="utf-8") as f:
        yaml.dump_all(citations_data, f, default_flow_style=False)

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/citations")
    assert response.status_code == 200
    assert response.json()["citations"] == citations_data


def test_get_citations_document_not_found(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET .../citations returns 404 when document doesn't exist."""

    response = client.get("/api/v1/libraries/test/documents/nonexistent/citations")
    assert response.status_code == 404
    assert response.json()["type"] == "/errors/document-not-found"


# =============================================================================
# POST /libraries/{library}/documents/{id}/citations
# =============================================================================


def test_fetch_citations_no_doi(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../citations returns 400 when document has no DOI."""

    papis_id, _ = create_test_document(client, title="No DOI")

    response = client.post(f"/api/v1/libraries/test/documents/{papis_id}/citations")
    assert response.status_code == 400
    assert response.json()["type"] == "/errors/citation-no-doi"


def test_fetch_citations_bad_doi(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../citations returns 400 when Crossref can't resolve DOI."""
    papis_id, _ = create_test_document(
        client,
        path="bad-doi-doc",
        title="Bad DOI",
        doi="10.1234/unresolvable",
    )

    with patch.object(
        papis.crossref, "get_data", side_effect=ValueError("DOI not found")
    ):
        response = client.post(f"/api/v1/libraries/test/documents/{papis_id}/citations")
    assert response.status_code == 400
    assert response.json()["type"] == "/errors/citation-fetch-empty"


def test_fetch_citations_document_not_found(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST .../citations returns 404 when document doesn't exist."""

    response = client.post("/api/v1/libraries/test/documents/nonexistent/citations")
    assert response.status_code == 404
    assert response.json()["type"] == "/errors/document-not-found"


# =============================================================================
# DELETE /libraries/{library}/documents/{id}/citations
# =============================================================================


def test_delete_citations(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """DELETE .../citations removes the citations file and GET returns []."""

    papis_id, doc_path = create_test_document(client)

    citations_file = os.path.join(tmp_config.libdir, doc_path, "citations.yaml")
    with open(citations_file, "w", encoding="utf-8") as f:
        yaml.dump_all([{"title": "Test"}], f, default_flow_style=False)
    assert os.path.exists(citations_file)

    response = client.delete(f"/api/v1/libraries/test/documents/{papis_id}/citations")
    assert response.status_code == 204

    assert not os.path.exists(citations_file)

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/citations")
    assert get_response.json() == {"citations": []}


def test_delete_citations_no_file(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """DELETE .../citations succeeds even when file doesn't exist."""

    papis_id, _ = create_test_document(client)

    response = client.delete(f"/api/v1/libraries/test/documents/{papis_id}/citations")
    assert response.status_code == 204


def test_delete_citations_document_not_found(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """DELETE .../citations returns 404 when document doesn't exist."""

    response = client.delete("/api/v1/libraries/test/documents/nonexistent/citations")
    assert response.status_code == 404
    assert response.json()["type"] == "/errors/document-not-found"


# =============================================================================
# GET /libraries/{library}/documents/{id}/cited-by
# =============================================================================


def test_get_cited_by_empty(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../cited-by returns [] when no cited-by file exists."""

    papis_id, _ = create_test_document(client)

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/cited-by")
    assert response.status_code == 200
    assert response.json() == {"cited_by": []}


def test_get_cited_by_with_data(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../cited-by returns data when cited-by file exists."""

    papis_id, doc_path = create_test_document(client)

    cited_by_data: list[dict[str, str]] = [
        {"title": "Citing Work", "doi": "10.1234/cites", "author": "Author"}
    ]

    cited_by_file = os.path.join(tmp_config.libdir, doc_path, "cited-by.yaml")
    with open(cited_by_file, "w", encoding="utf-8") as f:
        yaml.dump_all(cited_by_data, f, default_flow_style=False)

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/cited-by")
    assert response.status_code == 200
    assert response.json()["cited_by"] == cited_by_data


def test_get_cited_by_document_not_found(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET .../cited-by returns 404 when document doesn't exist."""

    response = client.get("/api/v1/libraries/test/documents/nonexistent/cited-by")
    assert response.status_code == 404
    assert response.json()["type"] == "/errors/document-not-found"


# =============================================================================
# POST /libraries/{library}/documents/{id}/cited-by
# =============================================================================


def test_fetch_cited_by_empty(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../cited-by returns [] when no documents cite this one."""

    papis_id, _ = create_test_document(client, doi="10.9999/uncited-doc")

    response = client.post(f"/api/v1/libraries/test/documents/{papis_id}/cited-by")
    assert response.status_code == 200
    assert response.json() == {"cited_by": []}


def test_fetch_cited_by_with_data(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../cited-by finds documents that cite this one."""

    # Doc A — the one being cited (has a DOI)
    doc_a_id, _ = create_test_document(
        client,
        path="cited-doc",
        title="Cited Document",
        doi="10.9999/cited-by-others",
    )

    # Doc B — the citing document (has citations.yaml referencing doc A's DOI)
    _doc_b_id, doc_b_path = create_test_document(
        client,
        path="citing-doc",
        title="Citing Document",
        doi="10.9999/citing-doc",
    )
    citations_data: list[dict[str, str]] = [
        {"title": "The Cited Work", "doi": "10.9999/cited-by-others", "author": "Doc A"}
    ]
    citations_file = os.path.join(tmp_config.libdir, doc_b_path, "citations.yaml")
    with open(citations_file, "w", encoding="utf-8") as f:
        yaml.dump_all(citations_data, f, default_flow_style=False)

    response = client.post(f"/api/v1/libraries/test/documents/{doc_a_id}/cited-by")
    assert response.status_code == 200
    result = response.json()["cited_by"]
    assert len(result) >= 1
    assert any(d.get("doi") == "10.9999/citing-doc" for d in result)


def test_fetch_cited_by_document_not_found(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST .../cited-by returns 404 when document doesn't exist."""

    response = client.post("/api/v1/libraries/test/documents/nonexistent/cited-by")
    assert response.status_code == 404
    assert response.json()["type"] == "/errors/document-not-found"


# =============================================================================
# DELETE /libraries/{library}/documents/{id}/cited-by
# =============================================================================


def test_delete_cited_by(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """DELETE .../cited-by removes the cited-by file and GET returns []."""

    papis_id, doc_path = create_test_document(client)

    cited_by_file = os.path.join(tmp_config.libdir, doc_path, "cited-by.yaml")
    with open(cited_by_file, "w", encoding="utf-8") as f:
        yaml.dump_all([{"title": "Test"}], f, default_flow_style=False)
    assert os.path.exists(cited_by_file)

    response = client.delete(f"/api/v1/libraries/test/documents/{papis_id}/cited-by")
    assert response.status_code == 204

    assert not os.path.exists(cited_by_file)

    get_response = client.get(f"/api/v1/libraries/test/documents/{papis_id}/cited-by")
    assert get_response.json() == {"cited_by": []}


def test_delete_cited_by_no_file(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """DELETE .../cited-by succeeds even when file doesn't exist."""

    papis_id, _ = create_test_document(client)

    response = client.delete(f"/api/v1/libraries/test/documents/{papis_id}/cited-by")
    assert response.status_code == 204


def test_delete_cited_by_document_not_found(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """DELETE .../cited-by returns 404 when document doesn't exist."""

    response = client.delete("/api/v1/libraries/test/documents/nonexistent/cited-by")
    assert response.status_code == 404
    assert response.json()["type"] == "/errors/document-not-found"
