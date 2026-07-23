from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from tests.server.test_documents import create_test_document

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration


def test_list_libraries(tmp_config: TemporaryConfiguration) -> None:
    """GET /api/v1/libraries returns list of all libraries with only names."""
    import papis.config

    papis.config.set("server-local-mode", False)

    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["libraries"], list)
    assert len(data["libraries"]) == 1
    assert data["libraries"][0]["name"] == "test"
    # path is None in non-local mode
    assert data["libraries"][0]["path"] is None


def test_get_library(tmp_config: TemporaryConfiguration) -> None:
    """GET /api/v1/libraries/{library} returns library info with only name."""
    import papis.config

    papis.config.set("server-local-mode", False)

    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries/test")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test"
    # path is None in non-local mode
    assert data["path"] is None


def test_get_library_not_found(tmp_config: TemporaryConfiguration) -> None:
    """GET /api/v1/libraries/{library} returns 404 for non-existent library."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries/nonexistent")

    assert response.status_code == 404


def test_list_libraries_includes_path_in_local_mode(
    tmp_config: TemporaryConfiguration,
) -> None:
    """Library paths are populated in local mode (the default)."""

    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["libraries"][0]["path"], str)
    assert data["libraries"][0]["path"]


def test_get_library_includes_path_in_local_mode(
    tmp_config: TemporaryConfiguration,
) -> None:
    """Library path is populated in local mode (the default)."""

    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries/test")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["path"], str)
    assert data["path"]


# =============================================================================
# GET /libraries/{library}/subfolders
# =============================================================================


def test_list_subfolders_empty(tmp_config: TemporaryConfiguration) -> None:
    """GET .../subfolders returns only '.' when library has no documents."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries/test/subfolders")

    assert response.status_code == 200
    data = response.json()
    assert data == {"subfolders": ["."]}


def test_list_subfolders_root_only(tmp_config: TemporaryConfiguration) -> None:
    """GET .../subfolders returns only '.' when all docs are at root."""
    from papis.server.app import app

    client = TestClient(app)
    create_test_document(client, path="doc-a", title="Doc A")
    create_test_document(client, path="doc-b", title="Doc B")

    response = client.get("/api/v1/libraries/test/subfolders")

    assert response.status_code == 200
    data = response.json()
    assert data == {"subfolders": ["."]}


def test_list_subfolders_nested(tmp_config: TemporaryConfiguration) -> None:
    """GET .../subfolders returns parent directories of all documents."""
    from papis.server.app import app

    client = TestClient(app)
    create_test_document(
        client, path="physics/relativity/doc1", title="Relativity Paper"
    )
    create_test_document(client, path="physics/doc2", title="Quantum Paper")
    create_test_document(client, path="math/doc3", title="Topology Paper")
    create_test_document(client, path="root-doc", title="Root Doc")

    response = client.get("/api/v1/libraries/test/subfolders")

    assert response.status_code == 200
    data = response.json()
    assert data == {"subfolders": [".", "math", "physics", "physics/relativity"]}


def test_list_subfolders_sorted(tmp_config: TemporaryConfiguration) -> None:
    """GET .../subfolders returns results in sorted order."""
    from papis.server.app import app

    client = TestClient(app)
    create_test_document(client, path="zebra/alpha", title="Zebra Alpha")
    create_test_document(client, path="alpha/beta", title="Alpha Beta")
    create_test_document(client, path="physics/gamma", title="Physics Gamma")

    response = client.get("/api/v1/libraries/test/subfolders")

    assert response.status_code == 200
    data = response.json()
    subfolders = data["subfolders"]
    assert subfolders == sorted(subfolders)
    assert subfolders[0] == "."
    assert "alpha" in subfolders
    assert "physics" in subfolders
    assert "zebra" in subfolders


def test_list_subfolders_library_not_found(
    tmp_config: TemporaryConfiguration,
) -> None:
    """GET .../subfolders returns 404 for non-existent library."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries/nonexistent/subfolders")

    assert response.status_code == 404
