"""ACM source handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from papis.crossref import find_doi
from papis.sources.handlers.web import WebsiteHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


_FILE_URL = "https://dl.acm.org/doi/pdf/{doi}"


class ACMHandler(WebsiteHandler):
    """Retrieve documents from `ACM <https://www.acm.org>`__.

    We get the DOI to construct the file URL and get metadata from Crossref.
    """

    name = "acm"
    url_or_id_re = re.compile(r".*acm\.org.*")
    enrich_from_doi = True

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:  # ruff: ignore[no-self-use]
        return {}

    def get_doi(self, evidence: LookupInput) -> str | None:
        return find_doi(self.url)

    def get_file_url(self, evidence: LookupInput) -> str | None:
        doi = self.get_doi(evidence)
        return _FILE_URL.format(doi=doi) if doi else None
