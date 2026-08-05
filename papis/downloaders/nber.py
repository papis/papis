from __future__ import annotations

import re

from papis.downloaders import Downloader


class NberDownloader(Downloader):
    """Importer from NBER working paper URLs."""

    _BASE_URL = "https://www.nber.org/"

    _BIBTEX_URL = "https://back.nber.org/bibliographic/{0}.bib"
    _PDF_URL = "https://www.nber.org/system/files/working_papers/{0}/{0}.pdf"

    def __init__(self, url: str) -> None:
        super().__init__(
            name="nber",
            uri=url,
            priority=10,
        )

    @classmethod
    def match(cls, url: str) -> NberDownloader | None:
        url = url.replace("http://", "https://")

        if "nber.org" in url:
            return NberDownloader(url)

        if re.match(r"^w\d+$", url):
            return NberDownloader(cls._BASE_URL + "/" + url)

        return None

    @property
    def nberid(self) -> str:
        match = re.search(r"w\d+", self.uri)
        assert match
        return match.group(0)

    def get_bibtex_url(self) -> str:
        return self._BIBTEX_URL.format(self.nberid)

    def get_document_url(self) -> str:
        return self._PDF_URL.format(self.nberid)
