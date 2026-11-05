"""IOPscience source handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import papis.config
from papis.crossref import find_doi
from papis.sources.handlers.web import WebsiteHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


_FILE_URL = "https://iopscience.iop.org/article/{doi}/pdf"
_BIBTEX_URL = (
    "https://iopscience.iop.org/export?type=article&doi={doi}"
    "&exportFormat=iopexport_bib"
    "&exportType=abs"
    "&navsubmit=Export+abstract"
)


class IOPscienceHandler(WebsiteHandler):
    """Retrieve documents from `IOPscience <https://iopscience.iop.org>`__.

    Scrapes the page's meta headers (plus the abstract and year). The DOI is derived
    from the URL and is used to build PDF and BibTeX URLs.
    """

    name = "iopscience"
    url_or_id_re = re.compile(r".*iopscience\.iop\.org.*")

    @classmethod
    def get_page_url_or_id(cls, input: str) -> str | None:
        input = input.replace("/pdf", "")
        return input if cls.url_or_id_re.search(input) else None

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:
        data = super().scrape(evidence)
        if not data:
            data = {}

        if evidence.content is not None:
            soup = self._get_soup(evidence.content)

            abstract_nodes = soup.find_all(
                "div", attrs={"class": "wd-jnl-art-abstract"}
            )
            if abstract_nodes:
                data["abstract"] = " ".join(a.text for a in abstract_nodes).strip()

        date = data.get("date")
        if date is not None:
            data["year"] = date.split("-")[0]

        return data

    def get_doi(self, evidence: LookupInput) -> str | None:
        return find_doi(self.url)

    def get_file_url(self, evidence: LookupInput) -> str | None:
        doc_url = self.data.get(papis.config.getstring("doc-url-key-name"))
        if doc_url:
            return str(doc_url)

        doi = self.data.get("doi")
        return _FILE_URL.format(doi=doi) if doi else None

    def get_bibtex_url(self, evidence: LookupInput) -> str | None:
        doi = self.data.get("doi")
        return _BIBTEX_URL.format(doi=doi) if doi else None
