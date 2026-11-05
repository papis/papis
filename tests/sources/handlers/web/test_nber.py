from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.sources.handler import FileReference, LookupInput
from papis.sources.handlers.web import nber
from tests.sources.helpers import assert_bibtex_followup, assert_match_cases

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration

NBER_URLS = (
    "https://www.nber.org/papers/w33843",
    "https://www.nber.org/papers/w29971",
)


def test_match() -> None:
    """URLs pointing at NBER are matched, others rejected."""
    assert_match_cases(
        nber.NberHandler,
        matched=(
            "https://www.nber.org/papers/w33843",
            "http://www.nber.org/papers/w29971",
            *NBER_URLS,
        ),
        rejected=(
            "https://www.nber.org/subscribe",
            "https://www.example.com/papers/w33843",
        ),
    )

    # a bare paper ID names a page: there is nothing to scrape, but the
    # identifier is enough to ask for the BibTeX export
    handler = nber.NberHandler.match_for_lookup(LookupInput(input="w33843"))
    assert handler is not None

    result = handler.lookup(LookupInput(input="w33843"))
    assert result.document is None
    assert_bibtex_followup(result, "https://back.nber.org/bibliographic/w33843.bib")


@pytest.mark.parametrize("url", NBER_URLS)
def test_lookup(tmp_config: TemporaryConfiguration, url: str) -> None:
    """The BibTeX export followup carries the document, the PDF link is
    derived from the paper ID in the URL."""
    evidence = LookupInput(input=url, kind="webpage", content="<html></html>")
    handler = nber.NberHandler.match_for_lookup(evidence)
    assert handler is not None

    result = handler.lookup(evidence)

    # no scraped data: the document arrives as the completed followup,
    # the PDF reference on the result itself
    assert result.document is None
    uid = url.rsplit("/", 1)[-1]
    assert result.files == [
        FileReference(
            extension="pdf",
            url=f"https://www.nber.org/system/files/working_papers/{uid}/{uid}.pdf",
        )
    ]
    assert_bibtex_followup(result, f"https://back.nber.org/bibliographic/{uid}.bib")
