from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import papis.crossref
from papis.sources.handler import FileReference, LookupInput
from papis.sources.handlers.web.worldscientific import WorldScientificHandler
from tests.sources.helpers import assert_match_cases

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration

WORLDSCIENTIFIC_URLS = (
    "https://www.worldscientific.com/doi/abs/10.1142/S0217984923501805",
    "https://www.worldscientific.com/doi/10.1142/S0217984923501805",
    "https://www.worldscientific.com/worldscibooks/10.1142/9789814560000_0001",
    "https://www.worldscientific.com/doi/10.1142/S0217984923501805?foo=bar",
)

#: (URL, DOI expected to be parsed out of it)
WORLDSCIENTIFIC_PAIRS = (
    (WORLDSCIENTIFIC_URLS[0], "10.1142/S0217984923501805"),
    (WORLDSCIENTIFIC_URLS[1], "10.1142/S0217984923501805"),
    (WORLDSCIENTIFIC_URLS[2], "10.1142/9789814560000_0001"),
    (WORLDSCIENTIFIC_URLS[3], "10.1142/S0217984923501805"),
)


def test_match() -> None:
    """URLs pointing at the site are matched, others rejected."""
    assert_match_cases(
        WorldScientificHandler,
        matched=(*WORLDSCIENTIFIC_URLS,),
        rejected=("https://worldscientific.co.uk/doi/10.1142/S0217984923501805",),
    )


@pytest.mark.parametrize(("url", "expected_doi"), WORLDSCIENTIFIC_PAIRS)
def test_lookup(
    tmp_config: TemporaryConfiguration,
    monkeypatch: pytest.MonkeyPatch,
    url: str,
    expected_doi: str,
) -> None:
    """The DOI in the URL (both the ``/doi/`` and the ``/worldscibooks/``
    form) keys the PDF link and is enriched with the doi source's metadata
    by the base class; URL syntax like the ``abs`` path segment or a query
    string is excluded from the DOI."""
    monkeypatch.setattr(
        papis.crossref, "doi_to_data", lambda doi: {"title": "A paper", "doi": doi}
    )

    evidence = LookupInput(input=url, kind="webpage", content="<html></html>")
    handler = WorldScientificHandler.match_for_lookup(evidence)
    assert handler is not None

    result = handler.lookup(evidence)
    assert result.document == {"doi": expected_doi, "title": "A paper"}
    assert result.followup is None
    assert result.files == [
        FileReference(
            extension="pdf",
            url=f"https://www.worldscientific.com/doi/pdf/{expected_doi}",
        )
    ]
