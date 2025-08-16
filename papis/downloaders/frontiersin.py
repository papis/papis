import re

import papis.downloaders.base


class Downloader(papis.downloaders.Downloader):
    """Retrieve documents from `Frontiers <https://www.frontiersin.org>`__"""

    def __init__(self, url: str) -> None:
        super().__init__(
            url, name="frontiersin",
            expected_document_extension="pdf",
            cookies={"gdpr": "true"},
            )

    @classmethod
    def match(cls, url: str) -> papis.downloaders.Downloader | None:
        if re.match(r".*frontiersin.org.*", url):
            return Downloader(url)
        else:
            return None

    def get_doi(self) -> str | None:
        url = self.uri
        self.logger.debug("Parsing DOI from '%s'.", url)
        mdoi = re.match(r".*/articles/([^/]+/[^/?&%^$]+).*", url)
        if mdoi:
            doi = mdoi.group(1)
            return doi
        return None

    def get_document_url(self) -> str | None:
        durl = f"https://www.frontiersin.org/articles/{self.get_doi()}/pdf"
        self.logger.debug("Using document URL: '%s'.", durl)
        return durl

    def get_bibtex_url(self) -> str | None:
        url = f"https://www.frontiersin.org/articles/{self.get_doi()}/bibTex"
        self.logger.debug("Using BibTeX URL: '%s'.", url)
        return url
