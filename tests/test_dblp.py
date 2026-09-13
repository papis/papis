from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
import requests

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

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


def get(code: int, url: str) -> requests.Response:
    assert url.startswith("https://dblp.org/rec")

    r = requests.Response()
    r.status_code = code
    return r


@pytest.mark.xfail(reason="dblp times out sometimes")
def test_valid_dblp_key(tmp_config: TemporaryConfiguration,
                        monkeypatch: pytest.MonkeyPatch,
                        has_connection: bool = True) -> None:
    from papis.dblp import is_valid_dblp_key

    with monkeypatch.context() as m:
        if not has_connection:
            m.setattr(requests.Session, "get", lambda self, url: get(200, url))

        for key in DBLP_KEYS_VALID:
            assert is_valid_dblp_key(key)

    with monkeypatch.context() as m:
        if not has_connection:
            m.setattr(requests.Session, "get", lambda self, url: get(404, url))

        for key in DBLP_KEYS_INVALID:
            assert not is_valid_dblp_key(key)


@pytest.mark.xfail(reason="dblp times out sometimes")
def test_importer_match(tmp_config: TemporaryConfiguration,
                        monkeypatch: pytest.MonkeyPatch,
                        has_connection: bool = True) -> None:
    from papis.dblp import DBLP_URL_FORMAT
    from papis.importer.dblp import DBLPImporter

    with monkeypatch.context() as m:
        if not has_connection:
            m.setattr(requests.Session, "get", lambda self, url: get(200, url))

        for key in DBLP_KEYS_VALID:
            url = DBLP_URL_FORMAT.format(uri=key)
            importer = DBLPImporter.match(url)
            assert importer is not None

            importer = DBLPImporter.match(key)
            assert importer is not None

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
