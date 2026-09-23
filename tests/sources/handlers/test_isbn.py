from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import papis.isbn
from papis.sources.handler import LookupInput, SearchInput
from papis.sources.handlers.isbn import IsbnHandler

if TYPE_CHECKING:
    from typing import Any

    from papis.testing import TemporaryConfiguration


@pytest.mark.parametrize(
    ("input_str", "expected_isbn"),
    [
        # matching normalizes to the canonical digit form: dashes, spaces
        # and other punctuation are dropped from the derived state
        ("9780486670478", "9780486670478"),
        ("0-7475-3269-9", "0747532699"),
        (" 0 7475 3269 9 ", "0747532699"),
        ("this-is-not-an-isbn", None),
        ("978048667047", None),  # wrong checksum length
        ("", None),
    ],
)
def test_match(input_str: str, expected_isbn: str | None) -> None:
    instance = IsbnHandler.match_for_lookup(LookupInput(input=input_str))
    if expected_isbn is None:
        assert instance is None
    else:
        assert instance is not None
        assert instance.isbn == expected_isbn


def test_lookup(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: dict[str, Any] = {}
    monkeypatch.setattr(
        papis.isbn,
        "get_data",
        lambda **kwargs: calls.update(kwargs) or [{"title": "T"}],
    )

    result = IsbnHandler("9780486670478").lookup(LookupInput(input="9780486670478"))

    assert result.document == {"title": "T"}
    assert calls["isbn_like"] == "9780486670478"


def test_search(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: dict[str, Any] = {}
    monkeypatch.setattr(
        papis.isbn,
        "get_data",
        lambda **kwargs: calls.update(kwargs) or [{"title": "T"}],
    )

    result = IsbnHandler.search(SearchInput(input="feynman diagrams"), max_results=1)

    assert result.documents[0]["title"] == "T"
    assert calls["query"] == "feynman diagrams"
    # the service is configured, not a per-call option
    assert "service" not in calls


def test_search_honors_max_results(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The search API's limit holds even if the service returns more (it may
    return several matches for a title query)."""
    monkeypatch.setattr(
        papis.isbn,
        "get_data",
        lambda **kwargs: [{"title": "First"}, {"title": "Second"}],
    )

    result = IsbnHandler.search(SearchInput(input="feynman diagrams"), max_results=1)
    assert result.documents == [{"title": "First"}]
