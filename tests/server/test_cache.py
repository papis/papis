from __future__ import annotations

import os
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

import papis.database

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


def test_clear_cache(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../cache resets the library cache and returns 204."""
    from papis.server.app import app

    client = TestClient(app)
    _, _ = create_test_document(client, path="cache-test", title="Cache Test")

    db = papis.database.get()
    cache_path = db.get_cache_path()
    assert os.path.exists(cache_path)

    response = client.delete("/api/v1/libraries/test/cache")
    assert response.status_code == 204
    assert os.path.exists(cache_path)


def test_clear_cache_library_not_found(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../cache returns 404 for non-existent library."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.delete("/api/v1/libraries/nonexistent/cache")

    assert response.status_code == 404


def test_clear_cache_mode_clear(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../cache?mode=clear clears the cache without rebuilding."""
    from papis.server.app import app

    client = TestClient(app)
    _, _ = create_test_document(
        client, path="cache-clear-test", title="Clear Mode Test"
    )

    db = papis.database.get()
    cache_path = db.get_cache_path()

    assert os.path.exists(cache_path)

    response = client.delete("/api/v1/libraries/test/cache?mode=clear")
    assert response.status_code == 204
    assert not os.path.exists(cache_path)


def test_clear_cache_invalid_mode(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../cache with an invalid mode returns 422."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.delete("/api/v1/libraries/test/cache?mode=invalid")
    assert response.status_code == 422
