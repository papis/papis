from __future__ import annotations

import re

from papis.downloaders import Downloader


class IEEEDownloader(Downloader):
    """Retrieve documents from `IEEE Xplore <https://ieeexplore.ieee.org>`__"""

    def __init__(self, url: str) -> None:
        super().__init__(url, name="ieee", expected_document_extension="pdf")

    @classmethod
    def match(cls, url: str) -> Downloader | None:
        m = re.match(r"^ieee:(.*)", url, re.IGNORECASE)
        if m:
            url = f"https://ieeexplore.ieee.org/document/{m.group(1)}"
            return IEEEDownloader(url)

        if re.match(r".*ieee.org.*", url):
            url = re.sub(r"\.pdf.*$", "", url)
            return IEEEDownloader(url)

        else:
            return None

    def get_identifier(self) -> str:
        m = re.search(r"ieeexplore\.ieee\.org/(?:abstract/)?document/(\d+)",
                      self.uri)
        if m:
            return m.group(1)

        m = re.search(r"[?&]arnumber=(\d+)", self.uri)
        if m:
            return m.group(1)

        m = re.match(r"^ieee:(\d+)$", self.uri, re.IGNORECASE)
        if m:
            return m.group(1)

        return self.uri

    def _get_bibtex_request(self) -> tuple[str, dict[str, object]]:
        identifier = self.get_identifier()
        bibtex_url = "https://ieeexplore.ieee.org/rest/search/citation/format"
        data = {
            "recordIds": [identifier],
            "download-format": "download-bibtex",
            "lite": True,
        }
        return bibtex_url, data

    def download_bibtex(self) -> None:
        import html
        import json

        url, params = self._get_bibtex_request()
        self.logger.debug("Using BibTeX URL: '%s'.", url)

        headers = {
            "Content-Type": "application/json",
            "X-Security-Request": "required",
            "Referer": self.uri,
        }
        response = self.session.post(url, json=params, headers=headers)
        if not response.ok:
            return

        # IEEE returns JSON ``{"data": "<bibtex...>"}`` (same shape Zotero
        # parses); the BibTeX itself may contain HTML entities / ``<br>``.
        try:
            payload = response.json()
        except json.JSONDecodeError:
            self.logger.debug("IEEE citation response was not JSON.")
            return

        bibtex = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(bibtex, str) or not bibtex.strip():
            self.logger.debug("IEEE citation JSON had no BibTeX in 'data'.")
            return

        self.bibtex_data = html.unescape(bibtex.replace("<br>", ""))

    def get_document_url(self) -> str | None:
        identifier = self.get_identifier()
        pdf_url = "{}{}{}".format(
            "https://ieeexplore.ieee.org/",
            "stampPDF/getPDF.jsp?tp=&isnumber=&arnumber=",
            identifier,
        )
        self.logger.debug("Using document URL: '%s'.", pdf_url)
        return pdf_url
