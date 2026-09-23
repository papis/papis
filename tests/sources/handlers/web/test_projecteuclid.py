from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.sources.handlers.web.projecteuclid import ProjectEuclidHandler
from tests.sources.helpers import (
    assert_bibtex_followup,
    assert_match_cases,
    lookup_page,
)

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

PROJECTEUCLID_URLS = (
    "https://projecteuclid.org/journals/advances-in-differential-equations/volume-19/issue-3_2f_4/An-analysis-of-the-renormalization-group-method-for-asymptotic-expansions/ade/1391109086.short",
    "https://projecteuclid.org/journals/duke-mathematical-journal/volume-164/issue-13/Delocalization-of-eigenvectors-of-random-matrices-with-independent-entries/10.1215/00127094-3129809.short",
)

#: BibTeX export link advertised by the saved pages, keyed by the record id
PROJECTEUCLID_BIBTEX_URLS = {
    "1391109086": "https://projecteuclid.org/citation/download/citation-ade19_245.bib",
    "00127094_3129809": "https://projecteuclid.org/citation/download/citation-dmj164_2507.bib",
}

#: PDF link advertised by the saved pages, keyed by the record id
PROJECTEUCLID_PDF_URLS = {
    "1391109086": "https://projecteuclid.org/journals/advances-in-differential-equations/"
    "volume-19/issue-3_2f_4/An-analysis-of-the-renormalization-group-"
    "method-for-asymptotic-expansions/ade/1391109086.pdf",
    "00127094_3129809": "https://projecteuclid.org/journals/duke-mathematical-journal/"
    "volume-164/issue-13/Delocalization-of-eigenvectors-of-random-matrices-"
    "with-independent-entries/10.1215/00127094-3129809.pdf",
}


def test_match() -> None:
    """URLs pointing at the site are matched, others rejected."""
    assert_match_cases(
        ProjectEuclidHandler,
        matched=("https://projecteuclid.org", *PROJECTEUCLID_URLS),
        rejected=("https://projecteuclid.co.uk/article/123",),
    )


@pytest.mark.parametrize("url", PROJECTEUCLID_URLS)
def test_lookup(
    tmp_config: TemporaryConfiguration, resource_cache: ResourceCache, url: str
) -> None:
    """Metadata is scraped from the saved page (as content, no network)."""
    uid = url.rsplit("/", 1)[-1].removesuffix(".short").replace("-", "_")
    result = lookup_page(
        ProjectEuclidHandler, resource_cache, f"ProjectEuclid_{uid}", url
    )

    assert result.files
    assert_bibtex_followup(result, PROJECTEUCLID_BIBTEX_URLS[uid])
