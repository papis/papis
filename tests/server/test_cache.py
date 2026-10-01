from __future__ import annotations

import os
from typing import TYPE_CHECKING

import papis.database

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

    from papis.testing import TemporaryConfiguration

from tests.server.conftest import create_test_document


def test_clear_cache(client: TestClient, tmp_config: TemporaryConfiguration) -> None:
    """DELETE .../cache resets the library cache and returns 204."""

    _, _ = create_test_document(client, path="cache-test", title="Cache Test")

    db = papis.database.get()
    cache_path = db.get_cache_path()
    assert os.path.exists(cache_path)

    response = client.delete("/api/v1/libraries/test/cache")
    assert response.status_code == 204
    assert os.path.exists(cache_path)


def test_clear_cache_library_not_found(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """DELETE .../cache returns 404 for non-existent library."""

    response = client.delete("/api/v1/libraries/nonexistent/cache")

    assert response.status_code == 404


def test_clear_cache_mode_clear(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """DELETE .../cache?mode=clear clears the cache without rebuilding."""

    _, _ = create_test_document(
        client, path="cache-clear-test", title="Clear Mode Test"
    )

    db = papis.database.get()
    cache_path = db.get_cache_path()

    assert os.path.exists(cache_path)

    response = client.delete("/api/v1/libraries/test/cache?mode=clear")
    assert response.status_code == 204
    assert not os.path.exists(cache_path)


def test_clear_cache_invalid_mode(
    client: TestClient, tmp_config: TemporaryConfiguration
) -> None:
    """DELETE .../cache with an invalid mode returns 422."""

    response = client.delete("/api/v1/libraries/test/cache?mode=invalid")
    assert response.status_code == 422
