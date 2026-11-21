from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest
import requests

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration


@pytest.mark.xfail(reason="remote pmid validity check can timeout")
def test_match(tmp_config: TemporaryConfiguration) -> None:
    from papis.importer.pubmed import PubMedImporter

    assert PubMedImporter.match("28012456")
    assert PubMedImporter.match("5503630")
    assert PubMedImporter.match("   1397  ")
    assert PubMedImporter.match("ABC1") is None
    assert PubMedImporter.match("1ABC") is None


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
