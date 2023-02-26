import re
from typing import Optional

import papis.downloaders.base


class Downloader(papis.downloaders.Downloader):

    def __init__(self, url: str) -> None:
        super().__init__(
            url, name="frontiersin",
            expected_document_extension="pdf",
            cookies={"gdpr": "true"},
            )

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        if re.match(r".*frontiersin.org.*", url):
            return Downloader(url)
        else:
            return None

    def get_doi(self) -> Optional[str]:
        url = self.uri
        self.logger.debug("Parsing DOI from '%s'.", url)
        mdoi = re.match(r".*/articles/([^/]+/[^/?&%^$]+).*", url)
        if mdoi:
            doi = mdoi.group(1)
            return doi
        return None

    def get_document_url(self) -> Optional[str]:
        durl = ("https://www.frontiersin.org/articles/{doi}/pdf"
                .format(doi=self.get_doi()))
        self.logger.debug("Using document URL: '%s'.", durl)
        return durl

    def get_bibtex_url(self) -> Optional[str]:
        url = ("https://www.frontiersin.org/articles/{doi}/bibTex"
               .format(doi=self.get_doi()))
        self.logger.debug("Using BibTeX URL: '%s'.", url)
        return url
