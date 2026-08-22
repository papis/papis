from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

    from fastapi.testclient import TestClient

    from papis.testing import TemporaryConfiguration


@pytest.fixture
def client(
    tmp_config: TemporaryConfiguration, request: pytest.FixtureRequest
) -> Iterator[TestClient]:
    """A FastAPI ``TestClient`` for the server app.

    Set ``raise_server_exceptions`` to ``False`` to test that unhandled exceptions are
    caught and returned as 500 errors:

        @pytest.mark.parametrize(
            "client", [{"raise_server_exceptions": False}], indirect=True
        )
        def test_something(client):
            ...
    """
    from fastapi.testclient import TestClient

    from papis.server.app import app

    raise_exc = True
    if hasattr(request, "param"):
        raise_exc = request.param.get("raise_server_exceptions", True)

    with TestClient(app, raise_server_exceptions=raise_exc) as c:
        yield c


def create_test_document(
    client: TestClient,
    path: str = "test-doc",
    title: str = "Test Document",
    **kwargs: object,
) -> tuple[str, str]:
    """Create a test document and return *(papis_id, path)*."""
    body: dict[str, object] = {"title": title, **kwargs}
    response = client.post(
        "/api/v1/libraries/test/documents",
        data={"metadata": json.dumps(body), "folder": path},
    )
    assert response.status_code == 201
    return response.json()["metadata"]["papis_id"], path


def populate_docs(client: TestClient, count: int, base_title: str = "Doc") -> list[str]:
    """Create *count* test documents and return their papis_ids."""
    ids: list[str] = []
    for i in range(count):
        id, _ = create_test_document(
            client,
            path=f"paged-{i:04d}",
            title=f"{base_title} {i:04d}",
            year=1950 + (i % 75),
        )
        ids.append(id)
    return ids
