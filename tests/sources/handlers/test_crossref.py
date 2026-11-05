from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import papis.crossref
from papis.exceptions import SourceError
from papis.sources.handler import LookupInput, SearchInput
from papis.sources.handlers.crossref import CrossrefHandler

if TYPE_CHECKING:
    from typing import Any

    from papis.testing import TemporaryConfiguration

DOI = "10.1103/physrevb.89.140501"


@pytest.mark.parametrize(
    ("evidence", "expected_title"),
    [
        (LookupInput(input="", fields={"title": "A title"}), "A title"),
        (LookupInput(input=DOI, fields={"title": "A title"}), "A title"),
        # without a title field there is no title query
        (LookupInput(input=""), None),
        (LookupInput(input=DOI), None),
        (LookupInput(input="", fields={"doi": DOI}), None),
        (LookupInput(input="", fields={"title": ""}), None),
    ],
)
def test_match(evidence: LookupInput, expected_title: str | None) -> None:
    instance = CrossrefHandler.match_for_lookup(evidence)
    if expected_title is None:
        assert instance is None
    else:
        assert instance is not None
        assert instance.title == expected_title


def test_lookup(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: dict[str, Any] = {}
    monkeypatch.setattr(
        papis.crossref,
        "get_data",
        lambda **kwargs: calls.update(kwargs) or [{"title": "One"}],
    )

    result = CrossrefHandler(title="some query").lookup(LookupInput(input="some query"))

    assert result.document is not None
    assert result.document == {"title": "One"}
    assert result.files == []
    # the title is passed as a field-scoped query, not free text
    assert calls["title"] == "some query"


def test_lookup_multiple_results(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        papis.crossref,
        "get_data",
        lambda **kwargs: [{"title": "One"}, {"title": "Two"}],
    )

    result = CrossrefHandler(title="some query").lookup(LookupInput(input="some query"))

    assert result.document is not None
    assert result.document["title"] == "One"
    assert "2 results" in (result.message or "")


def test_search_unknown_type(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A BibTeX type without a Crossref counterpart is reported by the handler
    instead of failing inside the API."""
    monkeypatch.setattr(papis.crossref, "get_data", lambda **kwargs: [])

    with pytest.raises(SourceError, match="unpublished"):
        CrossrefHandler.search(
            SearchInput(input="q", filters={"type": ["unpublished"]}), max_results=10
        )


def test_search(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: dict[str, Any] = {}
    monkeypatch.setattr(
        papis.crossref,
        "get_data",
        lambda **kwargs: calls.update(kwargs) or [{"title": "T"}],
    )

    query = SearchInput(
        input="gauge theory",
        filters={
            "author": ["Witten"],
            "type": ["article"],
            "journal": ["Nuclear Physics B"],
            "year": ["2024"],
            "doi": ["10.1016/0003-4916(86)90122-3"],
        },
    )
    result = CrossrefHandler.search(query, max_results=10)

    assert result.documents[0]["title"] == "T"
    assert calls["query"] == "gauge theory"
    assert calls["author"] == "Witten"
    assert calls["dois"] == ["10.1016/0003-4916(86)90122-3"]
    assert calls["max_results"] == 10
    # the canonical (BibTeX) type is translated to Crossref's vocabulary, a
    # year becomes a (partial date) range
    assert calls["filters"] == {
        "type": ["journal-article"],
        "container-title": ["Nuclear Physics B"],
        "from-pub-date": ["2024"],
        "until-pub-date": ["2024"],
    }
