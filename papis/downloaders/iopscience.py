import re
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(self, url)

    @classmethod
    def match(cls, url):
        """
        >>> Downloader.match(\
                'http://iopscience.iop.org/article/10.1088/0305-4470/24/2/004'\
            ) is False
        False
        >>> Downloader.match(\
                'blah://iop.org/!@#!@$!%!@%!$che.6b00559'\
            ) is False
        True
        >>> Downloader.match(\
                'iopscience.iop.com/!@#!@$!%!@%!$chemed.6b00559'\
            ) is False
        True
        """
        if re.match(r".*iopscience.iop.org.*", url):
            cleaned_url = re.sub(r"\/pdf$", "",
                re.sub(r"\/$", "", url)
            )
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
        # http://iopscience.iop.org/article/10.1088/0305-4470/24/2/004/pdf
        durl = self.getUrl()+"/pdf"
        self.logger.debug("[doc url] = %s" % durl)
        return durl

    def getAritcleId(self):
        """Get article's id for IOP
        :returns: Article id
        """
        url = self.getUrl()
        m = re.match(r"^.*iop.org/[^/]+/[^/]+/(.*)$", url)
        if not m:
            self.logger.error("Could not retrieve articleId from url")
            return None
        articleId = m.group(1)
        self.logger.debug("[doc articleId] = %s" % articleId)
        return articleId

    def getBibtexUrl(self):
        # http://iopscience.iop.org/export?articleId=0305-4470/24/2/004&exportFormat=iopexport_bib&exportType=abs&navsubmit=Export%2Babstract
        articleId = self.getAritcleId()
        url = "http://iopscience.iop.org/export?articleId=%s&exportFormat=iopexport_bib&exportType=abs&navsubmit=Export%%2Babstract" % articleId
        self.logger.debug("[bibtex url] = %s" % url)
        return url

# vim-run: python3 %
