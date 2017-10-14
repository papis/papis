import re
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(
            self, url, name="scitationaip"
        )
        self.expected_document_format = 'pdf'

    @classmethod
    def match(cls, url):
        # http://aip.scitation.org/doi/10.1063/1.4873138
        if re.match(r".*(aip|aapt).scitation.org.*", url):
            return Downloader(url)
        else:
            return False

    def get_doi(self):
        mdoi = re.match(r'.*/doi/(.*/[^?&%^$]*).*', self.get_url())
        if mdoi:
            doi = mdoi.group(1).replace("abs/", "").replace("full/", "")
            return doi
        else:
            return None

    def get_document_url(self):
        # http://aip.scitation.org/doi/pdf/10.1063/1.4873138
        durl = "http://aip.scitation.org/doi/pdf/%s" % self.get_doi()
        self.logger.debug("[doc url] = %s" % durl)
        return durl

    def get_bibtex_url(self):
        url = "http://aip.scitation.org/action/downloadCitation"\
              "?format=bibtex&cookieSet=1&doi=%s" % self.get_doi()
        self.logger.debug("[bibtex url] = %s" % url)
        return url
