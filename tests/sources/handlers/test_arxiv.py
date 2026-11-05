from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import papis.arxiv
from papis.sources.handler import LookupInput, SearchInput
from papis.sources.handlers.arxiv import ArxivHandler

if TYPE_CHECKING:
    from typing import Any

    from papis.testing import TemporaryConfiguration

PDF_URL = "https://arxiv.org/pdf/1701.08223"


@pytest.mark.parametrize(
    ("input_str", "expected_arxivid"),
    [
        # NOTE: the exhaustive extraction table lives in tests/test_arxiv.py;
        # this only pins that the handler delegates to it
        ("1701.08223", "1701.08223"),
        ("https://arxiv.org/abs/1305.2291v2", "1305.2291v2"),
        ("arXiv:1701.08223v2 [math.GT]", "1701.08223v2"),
        ("ARXIV:1701.08223", "1701.08223"),
        ("hep-th/9901001", "hep-th/9901001"),
        ("hello world", None),
        ("10.1103/PhysRevD.100.014501", None),
    ],
)
def test_match(input_str: str, expected_arxivid: str | None) -> None:
    instance = ArxivHandler.match_for_lookup(LookupInput(input=input_str))
    if expected_arxivid is None:
        assert instance is None
    else:
        assert instance is not None
        assert instance.arxivid == expected_arxivid


def test_match_uses_the_eprint_field() -> None:
    """An arXiv document stores its identifier as BibLaTeX ``eprint`` with
    ``eprinttype="arxiv"`` (e.g. from ``papis update --auto``)."""
    instance = ArxivHandler.match_for_lookup(
        LookupInput(fields={"eprint": "1701.08223", "eprinttype": "arxiv"})
    )
    assert instance is not None
    assert instance.arxivid == "1701.08223"

    # the type is case-insensitive
    instance = ArxivHandler.match_for_lookup(
        LookupInput(fields={"eprint": "arXiv:1701.08223v2", "eprinttype": "arXiv"})
    )
    assert instance is not None
    assert instance.arxivid == "1701.08223v2"

    # a conflicting type is authoritative: 'eprint' is a generic field
    assert (
        ArxivHandler.match_for_lookup(
            LookupInput(fields={"eprint": "1701.08223", "eprinttype": "zenodo"})
        )
        is None
    )

    # an untyped 'eprint' is typed by its shape (hand-edited documents)
    instance = ArxivHandler.match_for_lookup(
        LookupInput(fields={"eprint": "1701.08223"})
    )
    assert instance is not None
    assert instance.arxivid == "1701.08223"

    # ... so an untyped Zenodo/PMID-shaped eprint is still not claimed
    assert (
        ArxivHandler.match_for_lookup(LookupInput(fields={"eprint": "1234567"})) is None
    )

    # fields outrank the raw input
    instance = ArxivHandler.match_for_lookup(
        LookupInput(
            input="https://arxiv.org/abs/1305.2291",
            fields={"eprint": "1701.08223", "eprinttype": "arxiv"},
        )
    )
    assert instance is not None
    assert instance.arxivid == "1701.08223"


def test_match_uses_the_arxivid_field_alias() -> None:
    """``arxivid`` remains a legacy alias for older evidence/documents."""
    instance = ArxivHandler.match_for_lookup(
        LookupInput(fields={"arxivid": "1701.08223"})
    )
    assert instance is not None
    assert instance.arxivid == "1701.08223"

    # the field value may contain an identifier URL or prefix; it is normalized
    instance = ArxivHandler.match_for_lookup(
        LookupInput(fields={"arxivid": "arXiv:1701.08223v2"})
    )
    assert instance is not None
    assert instance.arxivid == "1701.08223v2"


def test_lookup(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = {"title": "A paper", "doc_url": PDF_URL}
    monkeypatch.setattr(papis.arxiv, "get_data", lambda **kwargs: [data])

    result = ArxivHandler("1701.08223").lookup(LookupInput(input="1701.08223"))

    assert result.document == data
    assert result.files[0].url == PDF_URL
    assert result.files[0].extension == "pdf"


def test_search(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: dict[str, Any] = {}
    monkeypatch.setattr(
        papis.arxiv,
        "get_data",
        lambda **kwargs: calls.update(kwargs) or [{"title": "T"}],
    )

    query = SearchInput(
        input="gauge theory",
        filters={
            "author": ["Witten"],
            "title": ["Gauge"],
            "category": ["cs.AI"],
            "eprint": ["1701.08223"],
            "arxivid": ["hep-th/9901001"],
        },
    )
    result = ArxivHandler.search(query, max_results=10)

    assert result.documents[0]["title"] == "T"
    assert calls["query"] == "gauge theory"
    assert calls["author"] == ["Witten"]
    assert calls["title"] == ["Gauge"]
    assert calls["category"] == ["cs.AI"]
    # 'eprint' (the document key) and 'arxivid' (the legacy spelling) both
    # constrain the identifier list, and their values are ORed
    assert calls["id_list"] == ["1701.08223", "hep-th/9901001"]
    assert calls["max_results"] == 10
