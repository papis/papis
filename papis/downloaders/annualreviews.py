import re
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(self, url)

    @classmethod
    def match(cls, url):
        #http://www.annualreviews.org/doi/blahblah/blahblah
        if re.match(r".*annualreviews.org.*", url):
            return Downloader(url)
        else:
            return False

    def getDoi(self):
        mdoi = re.match(r'.*annualreviews.org/doi/(.*)', self.getUrl())
        if mdoi:
            doi = mdoi.group(1).replace("abs/", "").replace("full/", "")
            self.logger.debug("[doi] = %s" % doi)
            return doi
        else:
            self.logger.error("Doi not found!!")

    def getDocumentUrl(self):
        # http://annualreviews.org/doi/pdf/10.1146/annurev-conmatphys-031214-014726
        durl = "http://annualreviews.org/doi/pdf/%s" % self.getDoi()
        self.logger.debug("[doc url] = %s" % durl)
        return durl

    def getBibtexUrl(self):
        # http://www.annualreviews.org/action/showCitFormats?doi=10.1146/annurev-conmatphys-031214-014726
        url = "http://annualreviews.org/action/downloadCitation"\
              "?format=bibtex&cookieSet=1&doi=%s" % self.getDoi()
        self.logger.debug("[bibtex url] = %s" % url)
        return url

# vim-run: python3 %
