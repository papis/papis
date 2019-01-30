import re
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(
            self, url, name="annualreviews"
        )
        self.expected_document_extension = 'pdf'

    @classmethod
    def match(cls, url):
        # http://www.annualreviews.org/doi/blahblah/blahblah
        if re.match(r".*annualreviews.org.*", url):
            return Downloader(url)
        else:
            return False

    def get_doi(self):
        mdoi = re.match(r'.*\.org/[^/]+/[^/]+/([^?]*)', self.get_url())
        if mdoi:
            doi = mdoi.group(1)
            self.logger.debug("[doi] = %s" % doi)
            return doi

    def get_document_url(self):
        # http://annualreviews.org/doi/pdf/
        # 10.1146/annurev-conmatphys-031214-014726
        durl = "http://annualreviews.org/doi/pdf/%s" % self.get_doi()
        self.logger.debug("[doc url] = %s" % durl)
        return durl

    def get_bibtex_url(self):
        # http://www.annualreviews.org/action/
        # showCitFormats?doi=10.1146/annurev-conmatphys-031214-014726
        url = "http://annualreviews.org/action/downloadCitation"\
              "?format=bibtex&cookieSet=1&doi=%s" % self.get_doi()
        self.logger.debug("[bibtex url] = %s" % url)
        return url
