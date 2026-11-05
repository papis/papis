from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any, Literal

import pytest
import requests

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

PUBMED_RESOURCEDIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "resources", "pubmed"
)


def _fake_session(pmid_responses: dict[str, int]) -> Any:
    """A session that returns a saved CSL response or a given status code."""
    import requests

    class FakeSession:
        def __init__(self) -> None:
            self.calls: list[tuple[str, Any]] = []

        def get(self, url: str, headers: Any = None) -> requests.Response:
            self.calls.append((url, headers))

            r = requests.Response()
            r.url = url
            pmid = url.rsplit("=", 1)[-1]

            status = pmid_responses.get(pmid, 404)
            r.status_code = status
            r._content = b""
            if status == 200:
                with open(
                    os.path.join(PUBMED_RESOURCEDIR, f"{pmid}.json"), encoding="utf-8"
                ) as fd:
                    r._content = fd.read().encode()

            return r

        def __enter__(self) -> FakeSession:
            return self

        def __exit__(self, *args: Any) -> Literal[False]:
            return False

    return FakeSession()


@pytest.mark.resource_setup(cachedir="resources/pubmed")
def test_get_data(
    tmp_config: TemporaryConfiguration,
    monkeypatch: pytest.MonkeyPatch,
    resource_cache: ResourceCache,
) -> None:
    """Checks that pubmed data is processed correctly."""
    import papis.pubmed
    import papis.utils

    session = _fake_session({"28012456": 200})
    monkeypatch.setattr(papis.utils, "get_session", lambda: session)

    data = papis.pubmed.get_data(" 28012456 ")

    expected = resource_cache.get_local_resource("28012456_out.json", data)
    assert data == expected
    assert len(session.calls) == 1
    assert session.calls[0][0].endswith("id=28012456")


@pytest.mark.xfail(reason="online service is flaky")
def test_get_data_online(tmp_config: TemporaryConfiguration) -> None:
    """Checks that data can be fetched from the online pubmed service."""
    from papis.pubmed import get_data

    data = get_data("28012456")
    assert data["title"]
    assert data["author_list"]


def _fake_response(status_code: int = 200, content: bytes = b"") -> Any:
    """Return a replacement for ``requests.Session.get``."""
    def get(self: Any, url: str, **kwargs: Any) -> requests.Response:
        response = requests.Response()
        response.url = url
        response.status_code = status_code
        response._content = content
        return response

    return get


def test_get_data_missing_pmid(tmp_config: TemporaryConfiguration,
                                monkeypatch: pytest.MonkeyPatch) -> None:
    """NCBI answers with a 200 and an empty list for an unknown PMID."""
    import papis.pubmed

    monkeypatch.setattr(requests.Session, "get", _fake_response(200, b"[]"))

    assert papis.pubmed.get_data("99999999") == {}


def test_get_data_404_is_error(tmp_config: TemporaryConfiguration,
                               monkeypatch: pytest.MonkeyPatch) -> None:
    """A 404 from this query endpoint means a broken URL, not a missing PMID."""
    import papis.pubmed
    from papis.exceptions import SourceError

    monkeypatch.setattr(requests.Session, "get", _fake_response(404))

    with pytest.raises(SourceError, match="Could not query PubMed"):
        papis.pubmed.get_data("99999999")


def test_get_data_valid(tmp_config: TemporaryConfiguration,
                        monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.pubmed

    content = json.dumps({
        "title": "Some title",
        "author": [{"family": "Knuth", "given": "Donald E."}],
    }).encode()
    monkeypatch.setattr(requests.Session, "get", _fake_response(200, content))

    data = papis.pubmed.get_data("99999999")
    assert data["title"] == "Some title"
    assert data["author"] == "Knuth, Donald E."


@pytest.mark.parametrize("status_code", [400, 500])
def test_get_data_http_error(tmp_config: TemporaryConfiguration,
                             monkeypatch: pytest.MonkeyPatch,
                             status_code: int) -> None:
    import papis.pubmed
    from papis.exceptions import SourceError

    monkeypatch.setattr(
        requests.Session, "get", _fake_response(status_code))

    with pytest.raises(SourceError, match="Could not query PubMed"):
        papis.pubmed.get_data("99999999")


@pytest.mark.parametrize("content", [b"<html>", b'"a string"'])
def test_get_data_invalid_response(tmp_config: TemporaryConfiguration,
                                   monkeypatch: pytest.MonkeyPatch,
                                   content: bytes) -> None:
    import papis.pubmed
    from papis.exceptions import SourceError

    monkeypatch.setattr(
        requests.Session, "get", _fake_response(200, content))

    with pytest.raises(SourceError, match="Unexpected response from PubMed"):
        papis.pubmed.get_data("99999999")
