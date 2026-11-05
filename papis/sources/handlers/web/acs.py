"""ACS Publications source handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from papis.sources.handlers.web import WebsiteHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


_BIBTEX_HREF_RE = re.compile(r"/Citation/Download\?.*citationFormat=2")


class ACSHandler(WebsiteHandler):
    """Retrieve documents from `ACS Publications <https://pubs.acs.org>`__.

    Scrapes meta headers and derives the PDF and BibTeX URLs from the scraped DOI.
    """

    name = "acs"
    url_or_id_re = re.compile(r".*acs\.org.*")

    def get_bibtex_url(self, evidence: LookupInput) -> str | None:
        if evidence.content is None:
            return None

        soup = self._get_soup(evidence.content)
        link = soup.find("a", href=_BIBTEX_HREF_RE)
        if link is None:
            return None

        from urllib.parse import urljoin

        return urljoin(self.url, str(link["href"]))
