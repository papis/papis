from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import papis.pubmed
from papis.sources.handler import LookupInput
from papis.sources.handlers.pmid import PmidHandler

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration


@pytest.mark.parametrize(
    ("input_str", "expected_pmid"),
    [
        ("28012456", "28012456"),
        # NOTE: the ID is stored raw, with whatever leading zeros it came
        # with (gather strips whitespace, the handler does not normalize)
        ("028012456", "028012456"),
        # an ISBN-13 shape is not a PMID
        ("9780486670478", None),
        # only the 978/979 prefixes are excluded
        ("1234567890123", "1234567890123"),
        ("ABC1", None),
        ("1ABC", None),
        ("13 97", None),
        ("", None),
    ],
)
def test_match(input_str: str, expected_pmid: str | None) -> None:
    instance = PmidHandler.match_for_lookup(LookupInput(input=input_str))
    if expected_pmid is None:
        assert instance is None
    else:
        assert instance is not None
        assert instance.pmid == expected_pmid


def test_lookup(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = {"title": "A paper", "author_list": [{"family": "Somebody"}]}
    monkeypatch.setattr(
        papis.pubmed, "get_data", lambda pmid: data if pmid == "28012456" else {}
    )

    result = PmidHandler("28012456").lookup(LookupInput(input="28012456"))
    assert result.document == data
