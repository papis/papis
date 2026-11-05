from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.sources.handler import FileReference
from papis.sources.handlers.web.acs import ACSHandler
from tests.sources.helpers import (
    assert_bibtex_followup,
    assert_match_cases,
    lookup_page,
)

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

ACS_URLS = (
    "https://pubs.acs.org/doi/abs/10.1021/jp003647e",
    "https://pubs.acs.org/doi/abs/10.1021/acscombsci.5b00087",
)

#: (PDF link, BibTeX export link) as advertised by the saved pages
ACS_LINKS = {
    "jp003647e": (
        "https://pubs.acs.org/jpcafh/article-pdf/105/13/3365/39010069/jp003647e.pdf",
        "https://pubs.acs.org/Citation/Download"
        "?resourceId=3527175&resourceType=3&citationFormat=2",
    ),
    "acscombsci.5b00087": (
        "https://pubs.acs.org/acsccc/article-pdf/18/1/1/8046824/co5b00087.pdf",
        "https://pubs.acs.org/Citation/Download"
        "?resourceId=784379&resourceType=3&citationFormat=2",
    ),
}


def test_match() -> None:
    """URLs pointing at the site are matched, others rejected."""
    assert_match_cases(
        ACSHandler,
        matched=("https://acs.org", *ACS_URLS),
        rejected=("https://acs.co.uk/article/123", "https://abs.org/article/123"),
    )


@pytest.mark.parametrize("url", ACS_URLS)
def test_lookup(
    tmp_config: TemporaryConfiguration, resource_cache: ResourceCache, url: str
) -> None:
    """Metadata is scraped from the saved page (as content, no network)."""
    from papis.bibtex import _bibtexparser_version  # ruff: ignore[import-private-name]

    if _bibtexparser_version() == "v1":
        pytest.skip("bibtexparser v1 composes accents differently")

    uid = url.rsplit("/", 1)[-1]
    pdf_url, bibtex_url = ACS_LINKS[uid]

    result = lookup_page(ACSHandler, resource_cache, f"ACS_{uid}", url)

    assert result.files == [FileReference(url=pdf_url, extension="pdf")]
    assert_bibtex_followup(result, bibtex_url)
