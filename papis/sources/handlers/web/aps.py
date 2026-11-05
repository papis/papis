"""APS source handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from papis.sources.handlers.web import WebsiteHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


class APSHandler(WebsiteHandler):
    """Retrieve documents from the `APS <https://journals.aps.org>`__ journals.

    The page's meta headers are scraped and the PDF and BibTeX URLs are derived from
    the page URL.
    """

    name = "aps"
    url_or_id_re = re.compile(r".*aps\.org.*")

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:
        data = super().scrape(evidence)
        if data and "url" not in data:
            data["url"] = evidence.input
        return data

    def get_file_url(self, evidence: LookupInput) -> str | None:
        return self.url.replace("/abstract", "/pdf")

    def get_bibtex_url(self, evidence: LookupInput) -> str | None:
        return f"{self.url.replace('/abstract', '/export')}?type=bibtex&download=true"
