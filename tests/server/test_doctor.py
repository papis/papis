from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from papis.testing import TemporaryConfiguration

from tests.server.conftest import create_test_document

# =============================================================================
# GET /libraries/{library}/doctor
# =============================================================================


def test_list_doctor_checks(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """GET .../doctor returns a list of available checks."""

    response = client.get("/api/v1/libraries/test/doctor")

    assert response.status_code == 200
    data = response.json()
    checks = data["checks"]
    assert isinstance(checks, list)
    assert len(checks) > 0
    for item in checks:
        assert isinstance(item["name"], str)


def test_list_doctor_checks_library_not_found(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET .../doctor returns 404 for non-existent library."""

    response = client.get("/api/v1/libraries/nonexistent/doctor")

    assert response.status_code == 404


# =============================================================================
# POST /libraries/{library}/doctor
# =============================================================================


def test_run_doctor_no_errors(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../doctor returns clean results when no errors are found."""

    papis_id, _ = create_test_document(client, path="doctor-clean")

    response = client.post(
        "/api/v1/libraries/test/doctor",
        params={"checks": ["refs"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert papis_id in data["results"]
    assert data["results"][papis_id] == []


def test_run_doctor_with_errors(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../doctor returns errors for documents with problems."""

    papis_id, _ = create_test_document(client, path="doctor-err")

    client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"metadata": {"ref": None}},
    )

    response = client.post(
        "/api/v1/libraries/test/doctor",
        params={"checks": ["refs"]},
    )

    assert response.status_code == 200
    data = response.json()
    errors = data["results"][papis_id]
    assert len(errors) == 1
    assert errors[0]["name"] == "refs"
    assert errors[0]["fix_available"] is True
    assert errors[0]["fixed"] is False


def test_run_doctor_with_fix(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../doctor with fix=true applies auto-fixers."""

    papis_id, _ = create_test_document(client, path="doctor-fix")

    client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"metadata": {"ref": None}},
    )

    response = client.post(
        "/api/v1/libraries/test/doctor",
        params={"checks": ["refs"], "fix": True},
    )

    assert response.status_code == 200
    data = response.json()
    errors = data["results"][papis_id]
    assert len(errors) == 1
    assert errors[0]["fixed"] is True

    doc_resp = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    assert doc_resp.status_code == 200
    assert doc_resp.json()["metadata"]["ref"] is not None


def test_run_doctor_all_docs_appear(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../doctor includes all queried documents in results, even clean ones."""

    id1, _ = create_test_document(client, path="doc1", title="One")
    id2, _ = create_test_document(client, path="doc2", title="Two")

    response = client.post(
        "/api/v1/libraries/test/doctor",
        params={"checks": ["refs"]},
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert id1 in results
    assert id2 in results


def test_run_doctor_with_query(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../doctor with query filters documents."""

    id1, _ = create_test_document(client, path="query-doc-1", title="Find Me")
    id2, _ = create_test_document(client, path="query-doc-2", title="Skip Me")

    response = client.post(
        "/api/v1/libraries/test/doctor",
        params={"checks": ["refs"], "query": 'title:"Find Me"'},
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert id1 in results
    assert id2 not in results


def test_run_doctor_unknown_check(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../doctor returns 404 for an unknown check name."""

    response = client.post(
        "/api/v1/libraries/test/doctor",
        params={"checks": ["nonexistent-check"]},
    )

    assert response.status_code == 404
    data = response.json()
    assert data["type"] == "/errors/check-not-found"


def test_run_doctor_library_not_found(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """POST .../doctor returns 404 for non-existent library."""

    response = client.post(
        "/api/v1/libraries/nonexistent/doctor",
        params={"checks": ["refs"]},
    )

    assert response.status_code == 404
