"""World Scientific source handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from papis.crossref import find_doi
from papis.sources.handlers.web import WebsiteHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


_FILE_URL = "https://www.worldscientific.com/doi/pdf/{doi}"


class WorldScientificHandler(WebsiteHandler):
    """Retrieve documents from `World Scientific <https://www.worldscientific.com>`__.

    No metadata is scraped. We get the PDF URL from the DOI in the page URL. The
    DOI is use to get metadata via Crossref.
    """

    name = "worldscientific"
    url_or_id_re = re.compile(r".*worldscientific\.com.*")
    enrich_from_doi = True

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:  # ruff: ignore[no-self-use]
        return {}

    def get_doi(self, evidence: LookupInput) -> str | None:
        return find_doi(self.url)

    def get_file_url(self, evidence: LookupInput) -> str | None:
        doi = self.get_doi(evidence)
        return _FILE_URL.format(doi=doi) if doi else None
