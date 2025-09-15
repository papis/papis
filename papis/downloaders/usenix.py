import re
from urllib.parse import urlparse

import papis.downloaders.base


def get_usenix_identifier(url: str) -> str | None:
    """
    >>> get_usenix_identifier("https://www.usenix.org/conference/usenixsecurity22/presentation/bulekov")
    'usenixsecurity22-bulekov'
    >>> get_usenix_identifier("https://www.usenix.org/conference/nsdi23/presentation/liu-tianfeng")
    'nsdi23-liu-tianfeng'
    """
    o = urlparse(url)
    path = o.path
    path_components = list(path.split("/"))
    if len(path_components) < 5:
        return None

    return f"{path_components[2]}-{path_components[4]}"


class Downloader(papis.downloaders.Downloader):
    """Retrieve documents from `USENIX <https://www.usenix.org>`__"""

    BIBTEX_URL_RE = re.compile(r"/biblio/export/bibtex/([0-9]+)$")

    def __init__(self, url: str):
        super().__init__(
            url,
            "usenix",
            expected_document_extension="pdf",
        )
        self.identifier = get_usenix_identifier(url)

    @classmethod
    def match(cls, url: str) -> papis.downloaders.Downloader | None:
        if re.match(r".*usenix.org/.*", url):
            return cls(url)
        else:
            return None

    def get_document_url(self) -> str | None:
        extension = (
            self.expected_document_extensions[0]
            if self.expected_document_extensions
            else ""
        )

        soup = self._get_soup()
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

    def get_bibtex_url(self) -> str | None:
        soup = self._get_soup()
        a = list(
            filter(
                lambda t: self.BIBTEX_URL_RE.match(t.get("href", "")),
                soup.find_all("a"),
            )
        )

        if not a:
            self.logger.warning(
                "No BibTeX URL found in this usenix page: '%s'.", self.uri
            )
            return None

        o = urlparse(self.uri)
        bib_path = a[0].get("href", "")
        bib_url = o._replace(path=bib_path)

        return bib_url.geturl()

    def download_bibtex(self) -> None:
        """Download and store that BibTeX data from :meth:`get_bibtex_url`.
        If that doesn't work, e.g., because CloudFlare does not like Papis for
        some reason, try to find the inline BibTeX content and use that instead.

        Use :meth:`get_bibtex_data` to access the metadata from the BibTeX URL.
        """
        bibtex_data = None
        url = self.get_bibtex_url()
        if url:
            self.logger.info("Downloading BibTeX from '%s'.", url)

            response = self.session.get(url, cookies=self.cookies)
            bibtex_data = response.content.decode().strip()
            if bibtex_data.startswith("<!DOCTYPE html>"):
                self.logger.debug("Downloaded BibTeX data:\n%s", self.bibtex_data)
                bibtex_data = None

        if bibtex_data is None:
            soup = self._get_soup()

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
                bibtex_data = text
            else:
                self.logger.debug(
                    "Failed to identify BibTeX content in USENIX HTML page!"
                )

        self.bibtex_data = bibtex_data
