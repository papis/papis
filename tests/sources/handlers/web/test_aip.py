from __future__ import annotations

from typing import TYPE_CHECKING

from papis.sources.handler import FileReference
from papis.sources.handlers.web.aip import AIPHandler
from tests.sources.helpers import (
    assert_bibtex_followup,
    assert_match_cases,
    lookup_page,
)

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

#: real pubs.aip.org article whose page (citation meta headers) is saved as a
#: resource
AIP_URL = (
    "https://pubs.aip.org/aip/pop/article/33/9/092505/3404740/"
    "The-toroidal-flux-and-separatrix-effects-in"
)
AIP_DOI = "10.1063/5.0347556"
AIP_PDF_URL = (
    "https://pubs.aip.org/aip/pop/article-pdf/doi/10.1063/5.0347556/"
    "21143342/092505_1_5.0347556.pdf"
)
AIP_BIBTEX_URL = (
    "https://pubs.aip.org/Citation/Download"
    "?resourceId=3404740&resourceType=3&citationFormat=2"
)


def test_match() -> None:
    """URLs pointing at pubs.aip.org are matched; the legacy Scitation
    domains and unrelated URLs are rejected."""
    assert_match_cases(
        AIPHandler,
        matched=(AIP_URL,),
        rejected=(
            "https://aip.org/doi/10.1063/1.4873138",
            "https://example.com/doi/10.1063/1.4873138",
            "https://aip.scitation.org/doi/10.1063/1.4873138",
            "https://aapt.scitation.org/doi/10.1119/1.5126830",
        ),
    )


def test_lookup(
    tmp_config: TemporaryConfiguration, resource_cache: ResourceCache
) -> None:
    """Metadata is scraped from the page's citation meta headers (with the
    site-relative ``og:url`` made absolute), the PDF link comes from
    ``citation_pdf_url``, and the export followup is keyed by the article id
    in the URL (as content, no network)."""
    name = f"AIP_{AIP_DOI.replace('/', '_')}"
    result = lookup_page(AIPHandler, resource_cache, name, AIP_URL)

    assert result.document is not None
    assert result.document["doi"] == AIP_DOI
    assert result.files == [FileReference(url=AIP_PDF_URL, extension="pdf")]
    assert_bibtex_followup(result, AIP_BIBTEX_URL)
