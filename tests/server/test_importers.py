"""
Tests for the importers API endpoints.

These tests verify the API contract: status codes, response shapes, and
error handling. They do NOT test importer correctness -- that lives in
``tests/test_importer.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from papis.plugin import PluginNotFoundError

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration


def _mock_importer(name: str, data: dict[str, Any]) -> MagicMock:
    """Create a mock importer with the given name and ctx.data."""
    m = MagicMock()
    m.name = name
    m.ctx.data = data
    m.ctx.files = []
    return m


# =============================================================================
# GET /api/v1/importers
# =============================================================================


def test_list_importers(tmp_config: TemporaryConfiguration) -> None:
    """GET /importers returns a list of importer names."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/importers")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all(isinstance(name, str) for name in data)
    assert "doi" in data
    assert "arxiv" in data
    assert "url" in data


# =============================================================================
# POST /api/v1/importers/match
# =============================================================================


def test_match_returns_empty_when_nothing_matches(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST /importers/match returns an empty list when nothing matches."""
    from papis.server.app import app

    with patch(
        "papis.server.routes.importers.get_matching_importers_by_uri",
        return_value=[],
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/importers/match",
            json={"uri": "this-does-not-match-anything"},
        )
        assert response.status_code == 200
        assert response.json()["matched"] == []


def test_match_passes_include_downloaders_false(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST /importers/match uses include_downloaders=False."""
    from papis.server.app import app

    with patch(
        "papis.server.routes.importers.get_matching_importers_by_uri",
        return_value=[],
    ) as mock_get:
        client = TestClient(app)
        response = client.post(
            "/api/v1/importers/match",
            json={"uri": "https://arxiv.org/abs/2301.00001"},
        )
        assert response.status_code == 200
        assert response.json()["matched"] == []
        mock_get.assert_called_once_with(
            "https://arxiv.org/abs/2301.00001", include_downloaders=False
        )


def test_match_importers_multiple(tmp_config: TemporaryConfiguration) -> None:
    """POST /importers/match returns all matched importer names."""
    from papis.server.app import app

    mock_importer1 = _mock_importer("url", {})
    mock_importer2 = _mock_importer("bibtex", {})

    with patch(
        "papis.server.routes.importers.get_matching_importers_by_uri",
        return_value=[mock_importer1, mock_importer2],
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/importers/match",
            json={"uri": "https://example.com/paper.bib"},
        )
        assert response.status_code == 200
        assert response.json()["matched"] == ["url", "bibtex"]


# =============================================================================
# POST /api/v1/importers/{name}/fetch
# =============================================================================


def test_fetch_unknown_importer_returns_404(tmp_config: TemporaryConfiguration) -> None:
    """POST /importers/{name}/fetch returns 404 for an unknown importer."""
    from papis.server.app import app

    with patch(
        "papis.server.routes.importers.get_importer_by_name",
        side_effect=PluginNotFoundError("papis.importer", "nonexistent"),
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/importers/nonexistent/fetch",
            json={"uri": "10.1234/test"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


def test_fetch_importer_does_not_match_returns_400(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST /importers/{name}/fetch returns 400 when the importer rejects the URI."""
    from papis.server.app import app

    mock_cls = MagicMock()
    # MagicMock().match(...) returns a MagicMock (truthy) by default,
    # so we must explicitly configure it to return None
    mock_cls.match.return_value = None

    with patch(
        "papis.server.routes.importers.get_importer_by_name",
        return_value=mock_cls,
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/importers/doi/fetch",
            json={"uri": "not-a-doi"},
        )
        assert response.status_code == 400


def test_fetch_network_error_returns_502(tmp_config: TemporaryConfiguration) -> None:
    """POST /importers/{name}/fetch returns 502 when the upstream source fails."""
    from papis.server.app import app

    mock_importer = _mock_importer("doi", {"title": "Test"})
    mock_cls = MagicMock()
    mock_cls.match.return_value = mock_importer

    with (
        patch(
            "papis.server.routes.importers.get_importer_by_name",
            return_value=mock_cls,
        ),
        patch(
            "papis.server.routes.importers.fetch_importers",
            return_value=[],  # fetch failed
        ),
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/importers/doi/fetch",
            json={"uri": "10.1234/test"},
        )
        assert response.status_code == 502


def test_fetch_importer_returns_no_data_returns_400(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST /importers/{name}/fetch returns 400 when the importer returns no data."""
    from papis.server.app import app

    mock_importer = _mock_importer("doi", {})
    mock_cls = MagicMock()
    mock_cls.match.return_value = mock_importer

    with (
        patch(
            "papis.server.routes.importers.get_importer_by_name",
            return_value=mock_cls,
        ),
        patch(
            "papis.server.routes.importers.fetch_importers",
            return_value=[mock_importer],
        ),
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/importers/doi/fetch",
            json={"uri": "10.1234/test"},
        )
        assert response.status_code == 400


def test_fetch_importer_returns_data(tmp_config: TemporaryConfiguration) -> None:
    """POST /importers/{name}/fetch returns importer name and fetched data."""
    from papis.server.app import app

    mock_importer = _mock_importer("doi", {"title": "Test Paper", "year": 2024})
    mock_cls = MagicMock()
    mock_cls.match.return_value = mock_importer

    with (
        patch(
            "papis.server.routes.importers.get_importer_by_name",
            return_value=mock_cls,
        ),
        patch(
            "papis.server.routes.importers.fetch_importers",
            return_value=[mock_importer],
        ),
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/importers/doi/fetch",
            json={"uri": "10.1234/test"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["importer"] == "doi"
        assert body["data"]["title"] == "Test Paper"
        assert body["data"]["year"] == 2024
