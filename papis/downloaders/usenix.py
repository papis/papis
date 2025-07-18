import re
from typing import Optional
from urllib.parse import urlparse

import papis.downloaders.base


class Downloader(papis.downloaders.Downloader):
    """Retrieve documents from `USENIX <https://www.usenix.org>`__"""

    def __init__(self, url: str):
        super().__init__(
            url,
            "usenix",
            expected_document_extension="pdf",
        )
        self._raw_data: Optional[str] = None

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        if re.match(r".*usenix.org/.*", url):
            return cls(url)
        else:
            return None

    def get_identifier(self) -> Optional[str]:
        """
        >>> d = Downloader("https://www.usenix.org/conference/usenixsecurity22/presentation/bulekov")
        >>> d.get_identifier()
        'usenixsecurity22-bulekov'
        >>> d = Downloader("https://www.usenix.org/conference/nsdi23/presentation/liu-tianfeng")
        >>> d.get_identifier()
        'nsdi23-liu-tianfeng'
        """  # noqa: E501
        o = urlparse(self.uri)
        path = o.path
        path_components = list(path.split("/"))
        if len(path_components) < 5:
            return None
        self.logger.debug("Parsed URL: %s.", path_components)
        return path_components[2] + "-" + path_components[4]

    def _ensure_raw_data(self) -> None:
        if not self._raw_data:
            resp = self.session.get(self.uri, cookies=self.cookies)
            self._raw_data = resp.content.decode("utf-8")
            if not self._raw_data:
                self.logger.warning("Failed to fetch data from '%s'.", self.uri)

    def get_document_url(self) -> Optional[str]:
        import bs4

        # make sure self._raw_data is available
        self._ensure_raw_data()
        if not self._raw_data:
            return None

        soup = bs4.BeautifulSoup(self._raw_data, "html.parser")
        extension = (
            self.expected_document_extensions[0]
            if self.expected_document_extensions
            else ""
        )

        a = list(
            filter(
                lambda t: (
                    t.get("name", "") == "citation_pdf_url"
                    and t.get("content", "").endswith(extension)
                ),
                soup.find_all("meta"),
            )
        )

        if not a:
            self.logger.warning(
                "No 'citation_pdf_url' URL found in this usenix page: '%s'.", self.uri
            )
            return None

        self.logger.debug("Found HTML tag: '%s'", a[0])
        pdf_url = str(a[0].get("content", default=""))
        if not pdf_url:
            return None

        return pdf_url.strip()

    def get_bibtex_url(self) -> Optional[str]:
        o = urlparse(self.uri)
        import bs4

        # make sure self._raw_data is available
        self._ensure_raw_data()
        if not self._raw_data:
            return None

        soup = bs4.BeautifulSoup(self._raw_data, "html.parser")
        re_matcher = re.compile(r"/biblio/export/bibtex/([0-9]+)$")

        a = list(
            filter(
                lambda t: re_matcher.match(t.get("href", "")),
                soup.find_all("a"),
            )
        )

        if not a:
            self.logger.warning(
                "No BibTeX URL found in this usenix page: '%s'.", self.uri
            )
            return None

        bib_path = a[0].get("href", "")
        bib_url = o._replace(path=bib_path)
        return bib_url.geturl()

    def download_bibtex(self) -> None:
        """Download and store that BibTeX data from :meth:`get_bibtex_url`.
        If that doesn't work, e.g., because cloudflare doesn't like papis for
        some reason, try to find the inline bibtex content and use that instead.

        Use :meth:`get_bibtex_data` to access the metadata from the BibTeX URL.
        """
        url = self.get_bibtex_url()
        if not url:
            return
        self.logger.info("Downloading BibTeX from '%s'.", url)

        response = self.session.get(url, cookies=self.cookies)
        self.bibtex_data = response.content.decode().strip()
        if self.bibtex_data.startswith("<!DOCTYPE html>"):
            self.logger.debug("Downloaded BibTeX data:\n%s", self.bibtex_data)
            self.bibtex_data = None

        if self.bibtex_data:
            return

        # fallback to trying to fetch the bibtex from the _raw_data itself
        # make sure self._raw_data is available
        self._ensure_raw_data()
        if not self._raw_data:
            return None
        # setup html parser
        import bs4

        soup = bs4.BeautifulSoup(self._raw_data, "html.parser")

        # find the bibtex div
        finds = list(
            filter(
                lambda t: "bibtex-text-entry" in t.get("class", ""),
                soup.find_all("div"),
            )
        )

        if finds:
            div = finds[0]
            text = div.text.replace("<br/>", "\n")
            self.bibtex_data = text
        else:
            self.logger.debug("Failed to identify BibTeX content in USENIX HTML page!")
