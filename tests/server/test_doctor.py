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
    import json

    response = client.post(
        "/api/v1/libraries/test/documents",
        data={"data": json.dumps({"title": title}), "folder": path},
    )
    assert response.status_code == 201
    return response.json()["document"]["papis_id"], path


# =============================================================================
# GET /libraries/{library}/doctor
# =============================================================================


def test_list_doctor_checks(tmp_config: TemporaryConfiguration) -> None:
    """GET .../doctor returns a list of available checks."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries/test/doctor")

    assert response.status_code == 200
    data = response.json()
    checks = data["checks"]
    assert isinstance(checks, list)
    assert len(checks) > 0
    for item in checks:
        assert isinstance(item["name"], str)


def test_list_doctor_checks_library_not_found(
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET .../doctor returns 404 for non-existent library."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries/nonexistent/doctor")

    assert response.status_code == 404


# =============================================================================
# POST /libraries/{library}/doctor
# =============================================================================


def test_run_doctor_no_errors(tmp_config: TemporaryConfiguration) -> None:
    """POST .../doctor returns clean results when no errors are found."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="doctor-clean")

    response = client.post(
        "/api/v1/libraries/test/doctor",
        params={"checks": ["refs"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert papis_id in data["results"]
    assert data["results"][papis_id] == []


def test_run_doctor_with_errors(tmp_config: TemporaryConfiguration) -> None:
    """POST .../doctor returns errors for documents with problems."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="doctor-err")

    client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"data": {"ref": None}},
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


def test_run_doctor_with_fix(tmp_config: TemporaryConfiguration) -> None:
    """POST .../doctor with fix=true applies auto-fixers."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="doctor-fix")

    client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"data": {"ref": None}},
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
    assert doc_resp.json()["document"]["ref"] is not None


def test_run_doctor_all_docs_appear(tmp_config: TemporaryConfiguration) -> None:
    """POST .../doctor includes all queried documents in results, even clean ones."""
    from papis.server.app import app

    client = TestClient(app)
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


def test_run_doctor_with_query(tmp_config: TemporaryConfiguration) -> None:
    """POST .../doctor with query filters documents."""
    from papis.server.app import app

    client = TestClient(app)
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


def test_run_doctor_unknown_check(tmp_config: TemporaryConfiguration) -> None:
    """POST .../doctor returns 404 for an unknown check name."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/libraries/test/doctor",
        params={"checks": ["nonexistent-check"]},
    )

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["code"] == "check_not_found"


def test_run_doctor_library_not_found(tmp_config: TemporaryConfiguration) -> None:
    """POST .../doctor returns 404 for non-existent library."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/libraries/nonexistent/doctor",
        params={"checks": ["refs"]},
    )

    assert response.status_code == 404
