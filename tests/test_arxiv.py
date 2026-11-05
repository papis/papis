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

#: Bare identifiers, i.e. the whole input is the id (modulo whitespace).
ARXIV_TEST_BARE_IDS = [
    "1701.08223",
    "1701.08223v2",
    "1205.0093",
    "hep-th/9901001",
    "math.GT/0309136",
    "cs/0111010",
    "HEP-TH/9901001",
    "  1701.08223  ",
    "hep-th/9901001\n",
]

#: Inputs that must not yield any identifier.
ARXIV_TEST_NO_IDS = [
    "1701.082231",                  # too many digits after the dot
    "1701.08223v",                  # version without a number
    "hep-th/990100",                # old style ids have exactly 7 digits
    "hep-th/99010012",
    "9901001",                      # old style without a category
    "2024.1234 embedded",           # not the whole input
    "In 2024.1234 we",
    "v2 1701.08223",
    "1701.08223, 1701.08224",       # two ids
    "10.1103/PhysRevD.100.014501",  # a DOI
    "1701.08223.pdf",
    "arXiv:2024.123456",            # too long, do not truncate
    "arXiv:my-cool-paper",
    "arXiv 1701.08223",             # marker without a separator
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
    assert client.searches[0].query == 'ti:"Finite Temperature" AND au:"Garnet Chan"'
    assert client.searches[0].max_results == 1


def test_get_data_query_construction(
        tmp_config: TemporaryConfiguration,
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Query terms are unencoded and multi-word values are phrases.

    The ``arxiv`` client URL-encodes the query itself, so pre-encoding a term
    here would double-encode it (and make it match nothing).
    """
    import papis.arxiv

    class FakeClient:
        def __init__(self) -> None:
            self.searches: list[arxiv.Search] = []

        def results(self, search: arxiv.Search) -> list[arxiv.Result]:
            self.searches.append(search)
            return []

    client = FakeClient()
    monkeypatch.setattr("arxiv.Client", lambda: client)

    papis.arxiv.get_data(query="gauge theory", max_results=1)
    papis.arxiv.get_data(
        author=["Witten", "Garnet Chan"], category="cs.AI", max_results=1)
    papis.arxiv.get_data(title='A "quoted" title', max_results=1)

    assert [search.query for search in client.searches] == [
        'all:"gauge theory"',
        '(au:Witten OR au:"Garnet Chan") AND cat:cs.AI',
        'ti:"A quoted title"',
    ]


def test_find_arxiv_id(tmp_config: TemporaryConfiguration) -> None:
    from papis.arxiv import find_arxivid_in_text

    for text, arxivid in ARXIV_TEST_URLS:
        assert find_arxivid_in_text(text) == arxivid, (
            f"Could not retrieve correct arxivid from {text}")

    for text in ARXIV_TEST_BARE_IDS:
        assert find_arxivid_in_text(text) == text.strip(), (
            f"Could not retrieve bare arxivid from {text}")

    for text in ARXIV_TEST_NO_IDS:
        assert find_arxivid_in_text(text) is None, (
            f"Unexpected arxivid retrieved from {text}")


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
