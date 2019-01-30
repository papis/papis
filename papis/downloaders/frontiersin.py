import re
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(
            self, url, name="frontiersin"
        )
        self.expected_document_extension = 'pdf'
        self.cookies = {
            'gdpr': 'true',
        }

    @classmethod
    def match(cls, url):
        if re.match(r".*frontiersin.org.*", url):
            return Downloader(url)
        else:
            return False

    def get_doi(self):
        url = self.get_url()
        self.logger.info('Parsing doi from {0}'.format(url))
        mdoi = re.match(r'.*/articles/([^/]+/[^/?&%^$]+).*', url)
        if mdoi:
            doi = mdoi.group(1)
            return doi
        return None

    def get_document_url(self):
        durl = "https://www.frontiersin.org/articles/{doi}/pdf".format(
            doi=self.get_doi())
        self.logger.debug("[doc url] = %s" % durl)
        return durl

    def get_bibtex_url(self):
        url = "https://www.frontiersin.org/articles/{doi}/bibTex".format(
            doi=self.get_doi())
        self.logger.debug("[bibtex url] = %s" % url)
        return url
