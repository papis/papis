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
        """
        o = urlparse(self.uri)
        path = o.path
        path_components = list(path.split("/"))
        if len(path_components) < 5:
            return None
        self.logger.debug("Parsed URL: %s.", path_components)
        return path_components[2] + "-" + path_components[4]

    def get_document_url(self) -> Optional[str]:
        """
        >>> d = Downloader("https://www.usenix.org/conference/usenixsecurity22/presentation/bulekov")
        >>> d.get_document_url()
        'https://www.usenix.org/system/files/sec22-bulekov.pdf'
        """

        import bs4

        if not self._raw_data:
            self._raw_data = self.session.get(self.uri).content.decode("utf-8")
            if not self._raw_data:
                self.logger.warning("Failed to fetch data from '%s'.", self.uri)
                return None

        soup = bs4.BeautifulSoup(self._raw_data, "html.parser")
        extension = (
            self.expected_document_extensions[0]
            if self.expected_document_extensions else "")

        a = list(
            filter(
                lambda t: (
                    t.get("name", "") == "citation_pdf_url"
                    and t.get("content", "").endswith(extension)
                ),
                soup.find_all("meta"),
            ))

        if not a:
            self.logger.warning(
                "No 'citation_pdf_url' URL found in this usenix page: '%s'.",
                self.uri)
            return None

        self.logger.debug("Found HTML tag: '%s'", a[0])
        pdf_url = str(a[0].get("content", default=""))
        if not pdf_url:
            return None

        return pdf_url.strip()

    def get_bibtex_url(self) -> Optional[str]:
        """
        >>> d = Downloader("https://www.usenix.org/conference/usenixsecurity22/presentation/bulekov")
        >>> d.get_document_url()
        'https://www.usenix.org/system/files/sec22-bulekov.pdf'
        >>> d.get_bibtex_url()
        'https://www.usenix.org/biblio/export/bibtex/277148'
        """
        o = urlparse(self.uri)
        import bs4

        if not self._raw_data:
            self._raw_data = self.session.get(self.uri).content.decode("utf-8")
            if not self._raw_data:
                self.logger.warning("Failed to fetch data from '%s'.", self.uri)
                return None

        soup = bs4.BeautifulSoup(self._raw_data, "html.parser")

        a = list(
            filter(
                lambda t: re.match(r"/biblio/export/bibtex/([0-9]+)$",
                                   t.get("href", "")),
                soup.find_all("a"),
            ))

        if not a:
            self.logger.warning("No BibTeX URL found in this usenix page: '%s'.",
                                self.uri)
            return None

        bib_path = a[0].get("href", "")
        bib_url = o._replace(path=bib_path)
        return bib_url.geturl()
