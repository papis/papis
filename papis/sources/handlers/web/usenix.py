"""USENIX source handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from papis.sources.handlers.web import WebsiteHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


_BIBTEX_HREF_RE = re.compile(r"/biblio/export/bibtex/([0-9]+)$")


class USENIXHandler(WebsiteHandler):
    """Retrieve documents from `USENIX <https://www.usenix.org>`__.

    The inline BibTeX data is scraped and the publisher BibTeX URL is derived in
    addition (when possible).
    """

    name = "usenix"
    url_or_id_re = re.compile(r".*usenix\.org/.*")

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:
        if evidence.content is None:
            return {}

        from papis.bibtex import bibtex_to_dict

        soup = self._get_soup(evidence.content)

        finds = list(
            filter(
                lambda t: "bibtex-text-entry" in t.get("class", ""),
                soup.find_all("div"),
            )
        )

        data: dict[str, Any] = {}
        if finds:
            text = finds[0].text.replace("<br/>", "\n")
            entries = bibtex_to_dict(text)
            if entries:
                data = dict(entries[0])

        return data

    def get_file_url(self, evidence: LookupInput) -> str | None:
        if evidence.content is None:
            return None

        suffix = f".{self.file_extension}" if self.file_extension else ""

        soup = self._get_soup(evidence.content)
        a = list(
            filter(
                lambda t: (
                    t.get("name", "") == "citation_pdf_url"
                    and t.get("content", "").endswith(suffix)
                ),
                soup.find_all("meta"),
            )
        )

        if not a:
            self.logger.debug(
                "No 'citation_pdf_url' URL found in this usenix page: '%s'.",
                self.url,
            )
            return None

        pdf_url = str(a[0].get("content", default=""))
        return pdf_url.strip() or None

    def get_bibtex_url(self, evidence: LookupInput) -> str | None:
        if evidence.content is None:
            return None

        from urllib.parse import urlparse

        soup = self._get_soup(evidence.content)
        a = list(
            filter(
                lambda t: _BIBTEX_HREF_RE.match(t.get("href", "")),
                soup.find_all("a"),
            )
        )

        if not a:
            self.logger.debug(
                "No BibTeX URL found in this usenix page: '%s'.", self.url
            )
            return None

        o = urlparse(self.url)
        bib_path = a[0].get("href", "")
        return o._replace(path=bib_path).geturl()
