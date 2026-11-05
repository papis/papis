from __future__ import annotations

from typing import TYPE_CHECKING

from papis.sources.handler import FileReference
from papis.sources.handlers.web.annualreviews import AnnualReviewsHandler
from tests.sources.helpers import (
    assert_bibtex_followup,
    assert_match_cases,
    lookup_page,
)

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

ANNUALREVIEWS_URL = (
    "https://www.annualreviews.org/content/journals/"
    "10.1146/annurev-conmatphys-031524-051559"
)
ANNUALREVIEWS_DOI = "10.1146/annurev-conmatphys-031524-051559"
ANNUALREVIEWS_UID = "annurev_conmatphys_031524_051559"

#: the page posts the (world-readable) full text to this form action
ANNUALREVIEWS_PDF_URL = (
    "https://www.annualreviews.org/deliver/fulltext/conmatphys/17/1/"
    "annurev-conmatphys-031524-051559.pdf"
    "?itemId=%2Fcontent%2Fjournals%2F10.1146%2Fannurev-conmatphys-031524-051559"
    "&mimeType=pdf&containerItemId=content/journals/conmatphys"
)
ANNUALREVIEWS_BIBTEX_URL = (
    f"https://www.annualreviews.org/content/journals/{ANNUALREVIEWS_DOI}/cite/bibtex"
)


def test_match() -> None:
    """URLs pointing at the site are matched, others rejected."""
    assert_match_cases(
        AnnualReviewsHandler,
        matched=("https://www.annualreviews.org", ANNUALREVIEWS_URL),
        rejected=("https://www.annualreviews.com", "https://www.yearlyreviews.com"),
    )


def test_lookup(
    tmp_config: TemporaryConfiguration, resource_cache: ResourceCache
) -> None:
    """Metadata is scraped from the page's meta headers and the PDF link from
    its full-text form action (as content, no network)."""
    result = lookup_page(
        AnnualReviewsHandler,
        resource_cache,
        f"AnnualReview_{ANNUALREVIEWS_UID}",
        ANNUALREVIEWS_URL,
    )

    assert result.files == [FileReference(url=ANNUALREVIEWS_PDF_URL, extension="pdf")]
    assert_bibtex_followup(result, ANNUALREVIEWS_BIBTEX_URL)
