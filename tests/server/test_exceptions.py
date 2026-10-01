"""Tests for exception handler normalisation to RFC 7807 format."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from papis.testing import TemporaryConfiguration


def test_api_error_is_rfc_7807(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """Standard ``APIError`` returns RFC 7807 format."""

    response = client.get("/api/v1/libraries/test/documents/nonexistent-id")

    assert response.status_code == 404
    body = response.json()
    assert body["type"] == "/errors/document-not-found"
    assert body["title"] == "Resource not found"
    assert body["status"] == 404
    assert "nonexistent-id" in body["detail"]
    assert response.headers["content-type"] == "application/problem+json"


def test_validation_error_is_rfc_7807(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """Pydantic validation errors return 422 in RFC 7807 format."""

    create_resp = client.post(
        "/api/v1/libraries/test/documents",
        data={
            "metadata": json.dumps({"title": "Validation Test"}),
            "folder": "validation-test",
        },
    )
    assert create_resp.status_code == 201
    papis_id = create_resp.json()["metadata"]["papis_id"]

    response = client.patch(
        f"/api/v1/libraries/test/documents/{papis_id}",
        json={"metadata": {"year": "not-a-number"}},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["type"] == "/errors/validation-error"
    assert body["title"] == "Validation error"
    assert body["status"] == 422
    assert "body.metadata.year" in body["detail"]
    assert "errors" in body["context"]
    assert isinstance(body["context"]["errors"], list)
    assert response.headers["content-type"] == "application/problem+json"


@pytest.mark.parametrize("client", [{"raise_server_exceptions": False}], indirect=True)
def test_unhandled_exception_is_rfc_7807(
    client: TestClient,
    tmp_config: TemporaryConfiguration,
) -> None:
    """An unhandled exception returns 500 in RFC 7807 format."""
    create_resp = client.post(
        "/api/v1/libraries/test/documents",
        data={
            "metadata": json.dumps({"title": "500 Test"}),
            "folder": "500-test",
        },
    )
    assert create_resp.status_code == 201
    papis_id = create_resp.json()["metadata"]["papis_id"]

    with patch(
        "papis.server.routes.documents.get_doc",
        side_effect=RuntimeError("simulated crash"),
    ):
        response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")

    assert response.status_code == 500
    body = response.json()
    assert body["type"] == "/errors/internal-server-error"
    assert body["title"] == "Internal server error"
    assert body["status"] == 500
    assert "bad state" in body["detail"] or "Try running" in body["detail"]
    assert response.headers["content-type"] == "application/problem+json"
