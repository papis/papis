from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.sources.handler import FileReference, LookupInput
from papis.sources.handlers.web.usenix import USENIXHandler
from tests.sources.helpers import (
    assert_bibtex_followup,
    assert_match_cases,
    lookup_page,
)

if TYPE_CHECKING:
    from typing import Any

    from papis.testing import ResourceCache, TemporaryConfiguration

USENIX_URLS = (
    "https://www.usenix.org/conference/usenixsecurity22/presentation/bulekov",
    "https://www.usenix.org/conference/nsdi22/presentation/goyal",
)

#: (PDF link, BibTeX export link) as advertised by the saved pages
USENIX_LINKS = {
    "bulekov": (
        "https://www.usenix.org/system/files/sec22-bulekov.pdf",
        "https://www.usenix.org/biblio/export/bibtex/277148",
    ),
    "goyal": (
        "https://www.usenix.org/system/files/nsdi22-paper-goyal.pdf",
        "https://www.usenix.org/biblio/export/bibtex/276958",
    ),
}


def _adjust_for_bibtexparser_v1(expected: dict[str, Any]) -> None:
    # NOTE: bibtexparser v1 keeps months as strings, unlike v2
    from papis.bibtex import _bibtexparser_version  # ruff: ignore[import-private-name]

    if _bibtexparser_version() == "v1":
        expected["month"] = {4: "April", 8: "August"}[expected["month"]]


def test_match() -> None:
    """URLs pointing at the site are matched, others rejected."""
    assert_match_cases(
        USENIXHandler,
        matched=("https://usenix.org/conference", *USENIX_URLS),
        rejected=("https://usewin.org/article/123", "https://usenix.com/article/123"),
    )


def test_lookup_without_links(tmp_config: TemporaryConfiguration) -> None:
    """A page without the PDF meta or BibTeX link contributes the scraped
    inline data only."""
    evidence = LookupInput(
        input=USENIX_URLS[0],
        kind="webpage",
        content=(
            "<html><head>"
            # no '.pdf' suffix: not a usable PDF link
            '<meta name="citation_pdf_url" content="https://example.com/paper">'
            "</head><body>"
            '<div class="bibtex-text-entry">'
            "@inproceedings{key, title = {Inline title}, author = {Somebody}}"
            "</div>"
            # not the export URL pattern
            '<a href="/biblio/export/other/277148">export</a>'
            "</body></html>"
        ),
    )
    handler = USENIXHandler.match_for_lookup(evidence)
    assert handler is not None

    result = handler.lookup(evidence)
    assert result.document is not None
    assert result.document["title"] == "Inline title"
    assert result.files == []
    assert result.followup is None


@pytest.mark.parametrize("url", USENIX_URLS)
def test_lookup(
    tmp_config: TemporaryConfiguration, resource_cache: ResourceCache, url: str
) -> None:
    """Metadata is scraped from the saved page (as content, no network)."""
    uid = url.rsplit("/", 1)[-1]
    pdf_url, bibtex_url = USENIX_LINKS[uid]
    result = lookup_page(USENIXHandler, resource_cache, f"USENIX_{uid}", url,
                         adjust_expected=_adjust_for_bibtexparser_v1)

    assert result.files == [FileReference(url=pdf_url, extension="pdf")]
    assert_bibtex_followup(result, bibtex_url)
