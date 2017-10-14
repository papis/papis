import re
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(
            self, url, name="iopscience"
        )
        self.expected_document_format = 'pdf'

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
            return Downloader(url)
        else:
            return False

    def get_doi(self):
        mdoi = re.match(r'.*annualreviews.org/doi/(.*)', self.get_url())
        if mdoi:
            doi = mdoi.group(1).replace("abs/", "").replace("full/", "")
            self.logger.debug("[doi] = %s" % doi)
            return doi
        else:
            self.logger.error("Doi not found!!")

    def get_document_url(self):
        # http://iopscience.iop.org/article/10.1088/0305-4470/24/2/004/pdf
        durl = self.get_url()+"/pdf"
        self.logger.debug("[doc url] = %s" % durl)
        return durl

    def getAritcleId(self):
        """Get article's id for IOP
        :returns: Article id
        """
        url = self.get_url()
        m = re.match(r"^.*iop.org/[^/]+/[^/]+/(.*)$", url)
        if not m:
            self.logger.error("Could not retrieve articleId from url")
            return None
        articleId = m.group(1)
        self.logger.debug("[doc articleId] = %s" % articleId)
        return articleId

    def get_bibtex_url(self):
        # http://iopscience.iop.org/export?articleId=0305-4470/24/2/004&exportFormat=iopexport_bib&exportType=abs&navsubmit=Export%2Babstract
        articleId = self.getAritcleId()
        url = "http://iopscience.iop.org/export?articleId=%s&exportFormat=iopexport_bib&exportType=abs&navsubmit=Export%%2Babstract" % articleId
        self.logger.debug("[bibtex url] = %s" % url)
        return url

# vim-run: python3 %
