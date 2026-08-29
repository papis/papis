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

DBLP_KEYS_VALID = [
    "books/sp/02/ST2002",
    "conf/iccg/EncarnacaoAFFGM93",
    "journals/aam/Davis23",
    "phd/dnb/Wein23",
    "series/sci/2023-1062",
]

DBLP_KEYS_INVALID = [
    "books/sp/02",
    "books/sp/02/ST2002-unknown",
    "series/sci",
]


@pytest.mark.xfail(reason="online service is flaky")
def test_valid_dblp_key_online(tmp_config: TemporaryConfiguration) -> None:
    """Checks that only real dblp keys validate."""
    from papis.dblp import is_valid_dblp_key

    for key in DBLP_KEYS_VALID:
        assert is_valid_dblp_key(key)

    for key in DBLP_KEYS_INVALID:
        assert not is_valid_dblp_key(key)


@pytest.mark.xfail(reason="online service is flaky")
def test_importer_match_online(tmp_config: TemporaryConfiguration) -> None:
    """Checks that only real dblp keys and URLs match."""
    from papis.dblp import DBLP_URL_FORMAT
    from papis.importer.dblp import DBLPImporter

    for key in DBLP_KEYS_VALID:
        url = DBLP_URL_FORMAT.format(uri=key)
        importer = DBLPImporter.match(url)
        assert importer is not None

        importer = DBLPImporter.match(key)
        assert importer is not None

    # NOTE: this relies on dblp.org answering non-ok status codes for well-shaped but
    # nonexistent keys
    for key in DBLP_KEYS_INVALID:
        importer = DBLPImporter.match(key)
        assert importer is None

    for url in [
            "https://dblp.net/rec/books/sp/02/ST2002.html",
            "https://dblp.org/rec/books/sp/02/ST2002.bib",
            ]:
        importer = DBLPImporter.match(url)
        assert importer is None


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


@pytest.mark.resource_setup(cachedir="resources/dblp")
def test_importer_fetch(tmp_config: TemporaryConfiguration,
                        monkeypatch: pytest.MonkeyPatch,
                        resource_cache: ResourceCache) -> None:
    from papis.dblp import DBLP_URL_FORMAT
    from papis.importer.dblp import DBLPImporter

    url = DBLP_URL_FORMAT.format(uri=DBLP_KEYS_VALID[-1])
    infile = "dblp_1.bib"
    outfile = "dblp_1_out.json"

    with monkeypatch.context() as m:
        importer = DBLPImporter.match(url)
        assert importer is not None

        m.setattr(importer, "_get_body", lambda url:
                    resource_cache.get_remote_resource(infile, url))

        importer.fetch()
        extracted_data = importer.ctx.data
        expected_data = resource_cache.get_local_resource(outfile, extracted_data)

        assert extracted_data == expected_data


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
