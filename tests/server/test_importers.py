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
# GET /api/v1/libraries/{library}/importers
# =============================================================================


def test_list_importers(tmp_config: TemporaryConfiguration) -> None:
    """GET /importers returns a list of importer names."""
    from papis.server.app import app

    client = TestClient(app)
    response = client.get("/api/v1/libraries/test/import")
    assert response.status_code == 200

    data = response.json()
    importers = data["importers"]
    assert isinstance(importers, list)
    assert len(importers) > 0
    assert all(isinstance(item["name"], str) for item in importers)
    assert "doi" in [item["name"] for item in importers]
    assert "arxiv" in [item["name"] for item in importers]
    assert "url" in [item["name"] for item in importers]


# =============================================================================
# POST /api/v1/libraries/{library}/importers/match
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
            "/api/v1/libraries/test/import/match",
            json={"uri": "this-does-not-match-anything"},
        )
        assert response.status_code == 200
        assert response.json() == {"matched": []}


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
            "/api/v1/libraries/test/import/match",
            json={"uri": "https://arxiv.org/abs/2301.00001"},
        )
        assert response.status_code == 200
        assert response.json() == {"matched": []}
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
            "/api/v1/libraries/test/import/match",
            json={"uri": "https://example.com/paper.bib"},
        )
        assert response.status_code == 200
        assert response.json() == {"matched": ["url", "bibtex"]}


# =============================================================================
# POST /api/v1/libraries/{library}/importers/fetch
# =============================================================================


def test_fetch_unknown_importer_returns_404(tmp_config: TemporaryConfiguration) -> None:
    """POST /importers/fetch returns 404 for an unknown importer name."""
    from papis.server.app import app

    with patch(
        "papis.server.routes.importers.get_available_importers",
        return_value=["doi", "arxiv"],
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/libraries/test/import/fetch",
            json={"uri": "10.1234/test"},
            params={"importers": ["nonexistent"]},
        )
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "importer_not_found"


def test_fetch_filesystem_importer_rejected(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST /importers/fetch rejects filesystem importers (folder, lib)."""
    from papis.server.app import app

    with patch(
        "papis.server.routes.importers.get_available_importers",
        return_value=["doi", "folder", "lib", "arxiv"],
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/libraries/test/import/fetch",
            json={"uri": "/tmp/doc"},
            params={"importers": ["folder"]},
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "local_mode_required"
        assert "folder" in response.json()["detail"]["message"]

    with patch(
        "papis.server.routes.importers.get_available_importers",
        return_value=["doi", "folder", "lib", "arxiv"],
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/libraries/test/import/fetch",
            json={"uri": "/tmp/doc"},
            params={"importers": ["lib", "folder"]},
        )
        assert response.status_code == 400
        assert "folder" in response.json()["detail"]["message"]
        assert "lib" in response.json()["detail"]["message"]


def test_fetch_no_importers_match_returns_400(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST /importers/fetch returns 400 when no importers can handle the URI."""
    from papis.server.app import app

    with (
        patch(
            "papis.server.routes.importers.get_available_importers",
            return_value=["doi"],
        ),
        patch(
            "papis.server.routes.importers.get_matching_importers_by_name",
            return_value=[],
        ),
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/libraries/test/import/fetch",
            json={"uri": "not-a-doi"},
            params={"importers": ["doi"]},
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "invalid_uri"


def test_fetch_no_importers_match_auto_returns_400(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST /importers/fetch returns 400 when auto-match finds no importers."""
    from papis.server.app import app

    with patch(
        "papis.server.routes.importers.get_matching_importers_by_uri",
        return_value=[],
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/libraries/test/import/fetch",
            json={"uri": "this-does-not-match-anything"},
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "invalid_uri"


def test_fetch_network_error_returns_502(tmp_config: TemporaryConfiguration) -> None:
    """POST /importers/fetch returns 502 when all upstream sources fail."""
    from papis.server.app import app

    mock_importer = _mock_importer("doi", {"title": "Test"})

    with (
        patch(
            "papis.server.routes.importers.get_matching_importers_by_uri",
            return_value=[mock_importer],
        ),
        patch(
            "papis.server.routes.importers.fetch_importers",
            return_value=[],  # fetch failed
        ),
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/libraries/test/import/fetch",
            json={"uri": "10.1234/test"},
        )
        assert response.status_code == 502


def test_fetch_importer_returns_no_data_returns_400(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST /importers/fetch returns 400 when the merged result has no data."""
    from papis.server.app import app

    mock_importer = _mock_importer("doi", {})

    with (
        patch(
            "papis.server.routes.importers.get_matching_importers_by_uri",
            return_value=[mock_importer],
        ),
        patch(
            "papis.server.routes.importers.fetch_importers",
            return_value=[mock_importer],
        ),
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/libraries/test/import/fetch",
            json={"uri": "10.1234/test"},
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "importer_no_data"


def test_fetch_single_importer_returns_data(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST /importers/fetch with a single importer returns data."""
    from papis.server.app import app

    mock_importer = _mock_importer("doi", {"title": "Test Paper", "year": 2024})

    with (
        patch(
            "papis.server.routes.importers.get_available_importers",
            return_value=["doi"],
        ),
        patch(
            "papis.server.routes.importers.get_matching_importers_by_name",
            return_value=[mock_importer],
        ),
        patch(
            "papis.server.routes.importers.fetch_importers",
            return_value=[mock_importer],
        ),
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/libraries/test/import/fetch",
            json={"uri": "10.1234/test"},
            params={"importers": ["doi"]},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["title"] == "Test Paper"
        assert body["data"]["year"] == 2024


def test_fetch_auto_match_returns_data(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST /importers/fetch without importers auto-matches and returns data."""
    from papis.server.app import app

    mock_importer = _mock_importer("doi", {"title": "Auto Matched"})

    with (
        patch(
            "papis.server.routes.importers.get_matching_importers_by_uri",
            return_value=[mock_importer],
        ),
        patch(
            "papis.server.routes.importers.fetch_importers",
            return_value=[mock_importer],
        ),
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/libraries/test/import/fetch",
            json={"uri": "10.1234/test"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["title"] == "Auto Matched"


def test_fetch_multiple_importers_merges_results(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST /importers/fetch with multiple importers merges their data."""
    from papis.server.app import app

    mock_doi = _mock_importer("doi", {"doi": "10.1234/test", "title": "From DOI"})
    mock_crossref = _mock_importer(
        "crossref", {"title": "From Crossref", "author": "Smith"}
    )

    with (
        patch(
            "papis.server.routes.importers.get_available_importers",
            return_value=["doi", "crossref"],
        ),
        patch(
            "papis.server.routes.importers.get_matching_importers_by_name",
            return_value=[mock_doi, mock_crossref],
        ),
        patch(
            "papis.server.routes.importers.fetch_importers",
            return_value=[mock_doi, mock_crossref],
        ),
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/libraries/test/import/fetch",
            json={"uri": "10.1234/test"},
            params={"importers": ["doi", "crossref"]},
        )
        assert response.status_code == 200
        body = response.json()
        # Later importer (crossref) overwrites 'title', both keys preserved
        assert body["data"]["title"] == "From Crossref"
        assert body["data"]["doi"] == "10.1234/test"
        assert body["data"]["author"] == "Smith"


def test_fetch_strips_ref_key(
    tmp_config: TemporaryConfiguration,
) -> None:
    """POST /importers/fetch strips the ref key via collect_from_importers."""
    from papis.server.app import app

    mock_importer = _mock_importer(
        "bibtex", {"title": "Test", "ref": "should-be-removed"}
    )

    with (
        patch(
            "papis.server.routes.importers.get_available_importers",
            return_value=["bibtex"],
        ),
        patch(
            "papis.server.routes.importers.get_matching_importers_by_name",
            return_value=[mock_importer],
        ),
        patch(
            "papis.server.routes.importers.fetch_importers",
            return_value=[mock_importer],
        ),
    ):
        client = TestClient(app)
        response = client.post(
            "/api/v1/libraries/test/import/fetch",
            json={"uri": "some.bib"},
            params={"importers": ["bibtex"]},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["title"] == "Test"
        assert "ref" not in body["data"]
