from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration


def test_list_libraries(tmp_config: TemporaryConfiguration) -> None:
    """GET /api/v1/libraries returns list of all libraries with only names."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "test"
    # path is not returned for security reasons
    assert "path" not in data[0]


def test_get_library(tmp_config: TemporaryConfiguration) -> None:
    """GET /api/v1/libraries/{library} returns library info with only name."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries/test")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test"
    # path is not returned for security reasons
    assert "path" not in data


def test_get_library_not_found(tmp_config: TemporaryConfiguration) -> None:
    """GET /api/v1/libraries/{library} returns 404 for non-existent library."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries/nonexistent")

    assert response.status_code == 404
