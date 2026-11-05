"""Project Euclid source handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from papis.sources.handlers.web import WebsiteHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


_BIBTEX_URL = "https://projecteuclid.org/citation/download/citation-{}.bib"


class ProjectEuclidHandler(WebsiteHandler):
    """Retrieve documents from `Project Euclid <https://projecteuclid.org>`__.

    Scrapes the page's meta headers and derives the BibTeX export URL from
    the scraped journal/volume/page identifiers.
    """

    name = "projecteuclid"
    url_or_id_re = re.compile(r".*projecteuclid\.org.*")

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:
        data = super().scrape(evidence)
        if data and "url" not in data:
            data["url"] = evidence.input
        return data

    def get_bibtex_url(self, evidence: LookupInput) -> str | None:
        try:
            # NOTE: this was determined heuristically by looking at the IDs
            # generated for a couple of papers and may change in the future
            identifier = "{}{}_{}".format(
                self.data["journal_abbrev"],
                self.data["volume"],
                self.data["firstpage"],
            )
            return _BIBTEX_URL.format(identifier)
        except KeyError:
            return None
