import re
import papis.downloaders.base

from typing import Optional


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url: str):
        papis.downloaders.base.Downloader.__init__(
            self, url, name="frontiersin")
        self.expected_document_extension = 'pdf'
        self.cookies = { 'gdpr': 'true', }

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.base.Downloader]:
        if re.match(r".*frontiersin.org.*", url):
            return Downloader(url)
        else:
            return None

    def get_doi(self) -> Optional[str]:
        url = self.uri
        self.logger.info('Parsing doi from {0}'.format(url))
        mdoi = re.match(r'.*/articles/([^/]+/[^/?&%^$]+).*', url)
        if mdoi:
            doi = mdoi.group(1)
            return doi
        return None

    def get_document_url(self) -> Optional[str]:
        durl = ("https://www.frontiersin.org/articles/{doi}/pdf"
                .format(doi=self.get_doi()))
        self.logger.debug("[doc url] = %s" % durl)
        return durl

    def get_bibtex_url(self) -> Optional[str]:
        url = ("https://www.frontiersin.org/articles/{doi}/bibTex"
               .format(doi=self.get_doi()))
        self.logger.debug("[bibtex url] = %s" % url)
        return url
