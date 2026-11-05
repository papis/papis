"""AIP Publishing source handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from papis.sources.handlers.web import WebsiteHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


_BIBTEX_URL = (
    "https://pubs.aip.org/Citation/Download"
    "?resourceId={id}&resourceType=3&citationFormat=2"
)

_ARTICLE_ID_RE = re.compile(r"/(\d{7,})(?:/[^/?#]+)?$")


class AIPHandler(WebsiteHandler):
    """Retrieve documents from `AIP Publishing <https://pubs.aip.org>`__.

    The page's citation meta headers contain the document data and the PDF link. The
    site's BibTeX export is fetched as a followup.
    """

    name = "aip"
    url_or_id_re = re.compile(r".*pubs\.aip\.org.*")

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:
        data = super().scrape(evidence)

        url = data.get("url")
        if url and url.startswith("/"):
            from urllib.parse import urljoin

            data["url"] = urljoin(self.url, url)

        return data

    def get_bibtex_url(self, evidence: LookupInput) -> str | None:
        mid = _ARTICLE_ID_RE.search(self.url)
        if mid:
            return _BIBTEX_URL.format(id=mid.group(1))

        return None
