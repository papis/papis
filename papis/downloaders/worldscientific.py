import re
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url: str):
        papis.downloaders.base.Downloader.__init__(
            self, url, name="worldscientific")
        self.expected_document_extension = 'pdf'
        self.cookies = { 'gdpr': 'true', }

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.base.Downloader]:
        if re.match(r".*worldscientific.com.*", url):
            return Downloader(url)
        else:
            return False

    def get_doi(self) -> Optional[str]:
        url = self.uri
        self.logger.debug('Parsing doi from {0}'.format(url))
        mdoi = re.match(r'.*/doi/(.*/[^?&%^$]*).*', url)
        if mdoi:
            doi = mdoi.group(1).replace("abs/", "").replace("full/", "")
            return doi

        mdoi = re.match(r'.*/worldscibooks/(.*/[^?&%^$]*).*', url)
        if mdoi:
            doi = mdoi.group(1).replace("abs/", "").replace("full/", "")
            return doi

        return None

    def get_document_url(self) -> Optional[str]:
        durl = ("https://www.worldscientific.com/doi/pdf/{doi}"
                .format(doi=self.get_doi()))
        self.logger.debug("[doc url] = %s" % durl)
        return durl

    def get_bibtex_url(self) -> Optional[str]:
        url = "https://www.worldscientific.com/action/downloadCitation"\
              "?format=bibtex&cookieSet=1&doi=%s" % self.get_doi()
        self.logger.debug("[bibtex url] = %s" % url)
        return url
