import re
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(
            self, url, name="iopscience"
        )
        self.expected_document_extension = 'pdf'

    @classmethod
    def match(cls, url):
        url = re.sub(r'/pdf', '', url)
        if re.match(r".*iopscience.iop.org.*", url):
            return Downloader(url)
        else:
            return False

    def get_doi(self):
        # http://iopscience.iop.org/article/10.1088/0305-4470/24/2/004?blah=1
        mdoi = re.match(r'.*\.org/[^/]+/([^?]*)', self.get_url())
        if mdoi:
            doi = mdoi.group(1).replace("abs/", "").replace("full/", "")
            self.logger.debug("[doi] = %s" % doi)
            return doi

    def get_document_url(self):
        # http://iopscience.iop.org/article/10.1088/0305-4470/24/2/004/pdf
        durl = 'https://iopscience.iop.org/article/{0}/pdf'.format(
            self.get_doi()
        )
        self.logger.debug("[doc url] = %s" % durl)
        return durl

    def _get_article_id(self):
        """Get article's id for IOP
        :returns: Article id
        """
        doi = self.get_doi()
        if doi:
            articleId = doi.replace('10.1088/', '')
            self.logger.debug("[doc articleId] = %s" % articleId)
            return articleId

    def get_bibtex_url(self):
        # http://iopscience.iop.org/export?
        # articleId=0305-4470/24/2/004&exportFormat=
        # iopexport_bib&exportType=abs&navsubmit=Export%2Babstract
        articleId = self._get_article_id()
        url = "{0}{1}{2}".format(
            "http://iopscience.iop.org/export?articleId=",
            articleId,
            "&exportFormat=iopexport_bib&exportType=abs"
            "&navsubmit=Export%2Babstract"
        )
        self.logger.debug("[bibtex url] = %s" % url)
        return url
