from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import pytest
import requests

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

DBLP_RESOURCEDIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "resources", "dblp"
)

# NOTE: the online tests are gone: the importer's entry point was pruned in
# Phase 3 of the importers refactor, and the `is_valid_*` online probes were
# removed as well; match-time existence verdicts are superseded by the
# (hermetic, syntactic) DblpHandler matching tests in
# tests/sources/handlers/test_dblp.py.


@pytest.mark.resource_setup(cachedir="resources/dblp")
def test_get_data(tmp_config: TemporaryConfiguration,
                  monkeypatch: pytest.MonkeyPatch,
                  resource_cache: ResourceCache,
                  ) -> None:
    """Checks that dblp data is processed correctly."""
    import papis.dblp

    saved = {
        ("johnson", "publ"): "publ_johnson.json",
        ("Comput. Educ.$", "venue"): "venue_Comput_Educ.json",
        ("Frontiers Virtual Real.$", "venue"): "venue_Frontiers_Virtual_Real.json",
        }

    def _search(query: str = "", output_format: str = "json",
                max_results: int = 30, max_completions: int = 10,
                api: str = "publ") -> str:
        fname = saved.get((query, api))
        assert fname is not None

        with open(os.path.join(DBLP_RESOURCEDIR, fname), encoding="utf-8") as fd:
            return fd.read()

    monkeypatch.setattr(papis.dblp, "search", _search)
    data = papis.dblp.get_data(query="johnson", max_results=2)

    expected = resource_cache.get_local_resource("get_data_out.json", data)
    assert data == expected


def _fake_response(status_code: int = 200, content: bytes = b"") -> Any:
    """Return a replacement for ``requests.Session.get``."""
    def get(self: Any, url: str, **kwargs: Any) -> requests.Response:
        response = requests.Response()
        response.url = url
        response.status_code = status_code
        response._content = content
        return response

    return get


def test_search_http_error(tmp_config: TemporaryConfiguration,
                           monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.dblp
    from papis.exceptions import SourceError

    monkeypatch.setattr(requests.Session, "get", _fake_response(500))

    with pytest.raises(SourceError, match="Could not query DBLP"):
        papis.dblp.search(query="test")


def test_get_data_no_results(tmp_config: TemporaryConfiguration,
                             monkeypatch: pytest.MonkeyPatch) -> None:
    import json as jsonlib

    import papis.dblp

    payload = {"result": {
        "status": {"code": 200, "text": "OK"},
        "hits": {"total": "0"},
        }}
    monkeypatch.setattr(
        papis.dblp, "search", lambda **kwargs: jsonlib.dumps(payload))

    assert papis.dblp.get_data(query="test") == []


def test_get_data_error_status(tmp_config: TemporaryConfiguration,
                               monkeypatch: pytest.MonkeyPatch) -> None:
    import json as jsonlib

    import papis.dblp
    from papis.exceptions import SourceError

    payload = {"result": {"status": {"code": 500, "text": "Invalid query"}}}
    monkeypatch.setattr(
        papis.dblp, "search", lambda **kwargs: jsonlib.dumps(payload))

    with pytest.raises(
            SourceError, match="Could not query DBLP: 'Invalid query'"):
        papis.dblp.get_data(query="test")


@pytest.mark.parametrize("response", ["<html>", "[1, 2, 3]", "{}"])
def test_get_data_invalid_response(tmp_config: TemporaryConfiguration,
                                   monkeypatch: pytest.MonkeyPatch,
                                   response: str) -> None:
    import papis.dblp
    from papis.exceptions import SourceError

    monkeypatch.setattr(papis.dblp, "search", lambda **kwargs: response)

    with pytest.raises(SourceError, match="Unexpected response from DBLP"):
        papis.dblp.get_data(query="test")
