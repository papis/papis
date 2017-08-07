import re
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(self, url)

    @classmethod
    def match(cls, url):
        # http://aip.scitation.org/doi/10.1063/1.4873138
        if re.match(r".*(aip|aapt).scitation.org.*", url):
            return Downloader(url)
        else:
            return False

    def getDoi(self):
        mdoi = re.match(r'.*scitation.org/doi/(.*)', self.getUrl())
        if mdoi:
            doi = mdoi.group(1).replace("abs/", "").replace("full/", "")
            self.logger.debug("[doi] = %s" % doi)
            return doi
        else:
            self.logger.error("Doi not found!!")

    def getDocumentUrl(self):
        # http://aip.scitation.org/doi/pdf/10.1063/1.4873138
        durl = "http://aip.scitation.org/doi/pdf/%s" % self.getDoi()
        self.logger.debug("[doc url] = %s" % durl)
        return durl

    def getBibtexUrl(self):
        url = "http://aip.scitation.org/action/downloadCitation"\
              "?format=bibtex&cookieSet=1&doi=%s" % self.getDoi()
        self.logger.debug("[bibtex url] = %s" % url)
        return url
