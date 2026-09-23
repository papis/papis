"""Springer source handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from papis.sources.handlers.web import WebsiteHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


_BIBTEX_URL = (
    "https://citation-needed.springer.com/v2/"
    "references/{doi}?format=bibtex&flavour=citation"
)


class SpringerHandler(WebsiteHandler):
    """Retrieve documents from `Springer <https://link.springer.com>`__.

    Scrapes the page's meta headers (that includes the PDF URL) and the BibTeX export
    URL is derived from the scraped DOI.
    """

    name = "springer"
    url_or_id_re = re.compile(r".*link\.springer\.com.*")

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:
        data = super().scrape(evidence)
        if "publication_date" in data:
            data["year"] = data["publication_date"].split("/")[0]
        return data

    def get_bibtex_url(self, evidence: LookupInput) -> str | None:
        doi = self.data.get("doi")
        return _BIBTEX_URL.format(doi=doi) if doi else None
