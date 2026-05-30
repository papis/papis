from __future__ import annotations

import os
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from papis.database.base import get_cache_file_path

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


def test_clear_cache(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../cache clears the library cache and returns 204."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(client, path="cache-test", title="Cache Test")

    cache_path = get_cache_file_path(tmp_config.libdir)

    client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    assert os.path.exists(cache_path)

    response = client.delete("/api/v1/libraries/test/cache")
    assert response.status_code == 204
    assert not os.path.exists(cache_path)


def test_clear_cache_rebuilds(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../cache clears cache, which is rebuilt on next request."""
    from papis.server.app import app

    client = TestClient(app)
    papis_id, _ = create_test_document(
        client, path="rebuild-test", title="Rebuild Test"
    )

    response = client.delete("/api/v1/libraries/test/cache")
    assert response.status_code == 204

    response = client.get(f"/api/v1/libraries/test/documents/{papis_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Rebuild Test"


def test_clear_cache_library_not_found(tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../cache returns 404 for non-existent library."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.delete("/api/v1/libraries/nonexistent/cache")

    assert response.status_code == 404
