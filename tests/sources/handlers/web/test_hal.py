from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.sources.handler import LookupInput
from papis.sources.handlers.web.hal import HALHandler
from tests.sources.helpers import (
    assert_bibtex_followup,
    assert_match_cases,
    lookup_page,
)

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

#: page URL and the BibTeX export derived from its scraped document URL
HAL_URLS = (
    ("https://hal.science/jpa-00235190", "https://hal.science/jpa-00235190/bibtex"),
    (
        "https://theses.hal.science/tel-02083632v1",
        "https://theses.hal.science/tel-02083632/bibtex",
    ),
)


def test_match() -> None:
    """URLs pointing at the site are matched, others rejected."""
    assert_match_cases(
        HALHandler,
        matched=(
            "https://hal.archives-ouvertes.fr/jpa-00235190",
            "https://tel.archives-ouvertes.fr/tel-02083632v1",
            "https://shs.hal.science/halshs-02285492",
            *(url for url, _ in HAL_URLS),
        ),
        rejected=(
            "https://data.archives-ouvertes.fr/hal-02285492",
            "https://data.hal.science/hal-02285492",
        ),
    )


@pytest.mark.parametrize(("url", "bibtex_url"), HAL_URLS)
def test_lookup(
    tmp_config: TemporaryConfiguration,
    resource_cache: ResourceCache,
    url: str,
    bibtex_url: str,
) -> None:
    """Metadata is scraped from the saved page (as content, no network)."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    domain = parsed.netloc.split(".")[0].upper()
    uid = parsed.path.rsplit("/", 1)[-1].replace("-", "_")
    result = lookup_page(HALHandler, resource_cache, f"HAL_{domain}_{uid}", url)

    assert result.files
    # the export URL is derived from the scraped document URL, which ends in
    # '/document', not from the page URL (which has no such suffix)
    assert_bibtex_followup(result, bibtex_url)


def test_no_bibtex_url_for_a_non_document_page(
    tmp_config: TemporaryConfiguration,
) -> None:
    """Only the '/document' page has a BibTeX export next to it: any other main
    file URL gets no followup instead of a guessed export URL (the file is still
    contributed)."""
    evidence = LookupInput(
        input="https://hal.science/jpa-00235190",
        kind="webpage",
        content=(
            '<html><meta name="citation_pdf_url" '
            'content="https://hal.science/jpa-00235190/file/paper.pdf" />'
            '<meta name="citation_title" content="A title" /></html>'
        ),
    )
    handler = HALHandler.match_for_lookup(evidence)
    assert handler is not None

    result = handler.lookup(evidence)
    assert result.followup is None
    assert [file.url for file in result.files] == [
        "https://hal.science/jpa-00235190/file/paper.pdf"
    ]
