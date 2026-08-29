from __future__ import annotations

import json
import os
from datetime import datetime
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    import arxiv

    from papis.testing import ResourceCache, TemporaryConfiguration

ARXIV_RESOURCEDIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "resources", "arxiv"
)

ARXIV_TEST_URLS = [
    ("/URI(https://arxiv.org/abs/1305.2291v2)>>", "1305.2291v2"),
    ("/URI(https://arxiv.org/abs/1205.0093)>>", "1205.0093"),
    ("/URI(https://arxiv.org/abs/1205.1494)>>", "1205.1494"),
    ("/URI(https://arxiv.org/abs/1011.2840)>>", "1011.2840"),
    ("/URI(https://arxiv.org/abs/1110.3658)>>", "1110.3658"),
    ("https://arxiv.org/abs/1110.3658>", "1110.3658"),
    ("http://arxiv.org/abs/1110.3658>", "1110.3658"),
    ("https://arxiv.com/abs/1110.3658>", "1110.3658"),
    ("https://arxiv.org/1110.3658>", "1110.3658"),
    ("arXiv:1701.08223v2?234", "1701.08223v2"),
    ("https://arxiv.org/pdf/1110.3658.pdf", "1110.3658"),
    ("http://arxiv.org/pdf/1110.3658.pdf", "1110.3658"),
    ("https://arxiv.com/pdf/1110.3658.pdf", "1110.3658"),
    ("http://arxiv.com/pdf/1110.3658.pdf", "1110.3658"),
]


def _load_arxiv_result() -> arxiv.Result:
    """Reconstruct a real :class:`arxiv.Result` from a captured API response."""
    import arxiv

    with open(os.path.join(ARXIV_RESOURCEDIR, "result.json"), encoding="utf-8") as fd:
        dump = json.load(fd)

    result = arxiv.Result(
        entry_id=dump["entry_id"],
        updated=datetime.fromisoformat(dump["updated"]),
        published=datetime.fromisoformat(dump["published"]),
        title=dump["title"],
        authors=[arxiv.Result.Author(a["name"]) for a in dump["authors"]],
        summary=dump["summary"],
        comment=dump["comment"],
        journal_ref=dump["journal_ref"],
        doi=dump["doi"],
        primary_category=dump["primary_category"],
        categories=dump["categories"],
        links=[arxiv.Result.Link(link["href"], title=link["title"], rel=link["rel"])
               for link in dump["links"]],
        )

    # NOTE: `pdf_url` is computed from the links in `arxiv` >= 4.0, but for backwards
    # compatibility we're setting it explicitly.
    if not getattr(result, "pdf_url", None):
        result.pdf_url = dump.get("pdf_url")

    return result


@pytest.mark.resource_setup(cachedir="resources/arxiv")
def test_arxiv_to_papis(tmp_config: TemporaryConfiguration,
                        resource_cache: ResourceCache,
                        ) -> None:
    from papis.arxiv import arxiv_to_papis

    data = arxiv_to_papis(_load_arxiv_result())
    expected = resource_cache.get_local_resource("arxiv_to_papis_out.json", data)
    assert data == expected


@pytest.mark.resource_setup(cachedir="resources/arxiv")
def test_get_data(tmp_config: TemporaryConfiguration,
                  monkeypatch: pytest.MonkeyPatch,
                  resource_cache: ResourceCache,
                  ) -> None:
    """Checks that arxiv data is processed correctly."""
    import papis.arxiv

    result = _load_arxiv_result()

    class FakeClient:
        def __init__(self) -> None:
            self.searches: list[arxiv.Search] = []

        def results(self, search: arxiv.Search) -> list[arxiv.Result]:
            self.searches.append(search)
            return [result]

    client = FakeClient()
    monkeypatch.setattr("arxiv.Client", lambda: client)

    data = papis.arxiv.get_data(
        author="Garnet Chan",
        title="Finite Temperature",
        max_results=1)

    expected = resource_cache.get_local_resource("get_data_out.json", data)
    assert data == expected
    assert len(client.searches) == 1
    assert client.searches[0].query == "ti:Finite%20Temperature AND au:Garnet%20Chan"
    assert client.searches[0].max_results == 1


def test_find_arxiv_id(tmp_config: TemporaryConfiguration) -> None:
    from papis.arxiv import find_arxivid_in_text

    for url, arxivid in ARXIV_TEST_URLS:
        assert find_arxivid_in_text(url) == arxivid, (
            f"Could not retrieve correct arxivid from {url}")


def test_downloader_match(tmp_config: TemporaryConfiguration) -> None:
    from papis.arxiv import ARXIV_ABS_URL
    from papis.downloaders.arxiv import ArxivDownloader

    down = ArxivDownloader.match("arxiv.org/sdf")
    assert isinstance(down, ArxivDownloader)

    down = ArxivDownloader.match("arxiv.com/!@#!@$!%!@%!$chemed.6b00559")
    assert down is None

    for uri, arxivid in ARXIV_TEST_URLS[-2:]:
        down = ArxivDownloader.match(uri)
        assert isinstance(down, ArxivDownloader)
        assert down
        assert down.arxivid == arxivid
        assert down.uri == f"{ARXIV_ABS_URL}/{arxivid}"


@pytest.mark.xfail(reason="online service is flaky")
@pytest.mark.parametrize("url", [
    "https://arxiv.org/abs/1001.3032",
    "https://arxiv.org/abs/1001.3032vunknown",
    ])
def test_importer_downloader_fetch_online(tmp_config: TemporaryConfiguration,
                                        url: str) -> None:
    """End-to-end fetch against the online arxiv service."""
    from papis.downloaders import get_matching_downloaders
    from papis.downloaders.arxiv import ArxivDownloader

    downs = get_matching_downloaders(url)
    assert len(downs) >= 1

    down = downs[0]
    assert down.name == "arxiv"
    assert isinstance(down, ArxivDownloader)
    assert down.expected_document_extensions == ("pdf",)

    doc = down.get_document_data()
    if down.result:
        assert doc is not None
        assert down.check_document_format()
    else:
        assert down.arxivid is not None
        assert doc is None


@pytest.mark.xfail(reason="online service is flaky")
def test_validate_arxivid_online(tmp_config: TemporaryConfiguration) -> None:
    """Existence check against arxiv's online abstract pages."""
    from papis.arxiv import validate_arxivid
    # good
    validate_arxivid("1206.6272")
    validate_arxivid("1206.6272v1")
    validate_arxivid("1206.6272v2")

    # bad
    for bad in ["1206.6272v3", "blahv2"]:
        with pytest.raises(ValueError, match="not an arxivid"):
            validate_arxivid(bad)


def test_get_data_no_results(tmp_config: TemporaryConfiguration,
                             monkeypatch: pytest.MonkeyPatch) -> None:
    import arxiv

    import papis.arxiv

    class _Client:
        @staticmethod
        def results(search: object) -> list[object]:
            return []

    monkeypatch.setattr(arxiv, "Client", _Client)

    assert papis.arxiv.get_data(query="test") == []


@pytest.mark.parametrize("exc_type", ["arxiv", "requests"])
def test_get_data_error(tmp_config: TemporaryConfiguration,
                        monkeypatch: pytest.MonkeyPatch,
                        exc_type: str) -> None:
    import arxiv
    import requests

    import papis.arxiv
    from papis.exceptions import SourceError

    error: Exception = arxiv.ArxivError("http://export.arxiv.org", 0, "boom")
    if exc_type == "requests":
        error = requests.ConnectionError("no route to host")

    class _Client:
        @staticmethod
        def results(search: object) -> list[object]:
            raise error

    monkeypatch.setattr(arxiv, "Client", _Client)

    with pytest.raises(SourceError, match="Could not query arXiv"):
        papis.arxiv.get_data(query="test")
