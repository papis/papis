"""Annual Reviews source handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import papis.config
from papis.sources.handlers.web import WebsiteHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


_BIBTEX_URL = "https://www.annualreviews.org/content/journals/{doi}/cite/bibtex"

# The file is offered as a form post target while the absolute docserver URL it leads
# to expires. For this reason we keep the stable form action.
_PDF_FORM_RE = re.compile(r"^/deliver/fulltext/.*\.pdf")


class AnnualReviewsHandler(WebsiteHandler):
    """Retrieve documents from `Annual Reviews <https://www.annualreviews.org>`__.

    Scrapes the page's meta headers. The PDF link is the page's full-text form action
    and the BibTeX URL is derived from the scraped DOI.
    """

    name = "annualreviews"
    url_or_id_re = re.compile(r".*annualreviews\.org.*")

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:
        data = super().scrape(evidence)
        if not data or evidence.content is None:
            return data

        soup = self._get_soup(evidence.content)

        pdf = soup.find("form", action=_PDF_FORM_RE)
        if pdf is not None:
            from urllib.parse import urljoin

            data[papis.config.getstring("doc-url-key-name")] = urljoin(
                self.url, str(pdf["action"])
            )

        return data

    def get_bibtex_url(self, evidence: LookupInput) -> str | None:
        doi = self.data.get("doi")
        return _BIBTEX_URL.format(doi=doi) if doi else None
