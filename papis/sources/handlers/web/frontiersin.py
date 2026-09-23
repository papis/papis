"""Frontiers source handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from urllib.parse import urljoin

from papis.crossref import DOI_PATTERN, find_doi
from papis.sources.handlers.web import WebsiteHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


#: The site may have trailing ``/full`` or ``/pdf``, requiring a custom pattern.
_DOI_URL_RE = re.compile(
    rf"frontiersin\.org.*?/articles/(?P<doi>{DOI_PATTERN}?)"
    r"(?=/(?:full|pdf)(?:[/?#]|$))"
)
_FILE_URL = "https://www.frontiersin.org/articles/{doi}/pdf"
_BIBTEX_HREF_RE = re.compile(r"/bibtex(?:$|[?#])", re.IGNORECASE)


class FrontiersInHandler(WebsiteHandler):
    """Retrieve documents from `Frontiers <https://www.frontiersin.org>`__.

    The page's citation meta headers are scraped and the DOI is used to build the PDF
    URL. The site's BibTeX URL is scraped from the article page.
    """

    name = "frontiersin"
    url_or_id_re = re.compile(r".*frontiersin\.org.*")

    def get_doi(self, evidence: LookupInput) -> str | None:
        match = _DOI_URL_RE.search(self.url)
        if match is not None:
            return match.group("doi")

        return find_doi(self.url)

    def get_file_url(self, evidence: LookupInput) -> str | None:
        doi = self.data.get("doi")
        return _FILE_URL.format(doi=doi) if doi else None

    def get_bibtex_url(self, evidence: LookupInput) -> str | None:
        if evidence.content is None:
            return None

        for anchor in self._get_soup(evidence.content).find_all("a", href=True):
            href = str(anchor["href"])
            if _BIBTEX_HREF_RE.search(href):
                return urljoin(self.url, href)

        return None
