import re
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(
            self, url, name="iopscience"
        )
        self.expected_document_extension = 'pdf'
        self.priority = 10

    @classmethod
    def match(cls, url):
        url = re.sub(r'/pdf', '', url)
        if re.match(r".*iopscience\.iop\.org.*", url):
            return Downloader(url)
        else:
            return False

    def get_doi(self):
        return self.ctx.data.get('doi')

    def get_document_url(self):
        if 'pdf_url' in self.ctx.data:
            return self.ctx.data.get('pdf_url')
        doi = self.get_doi()
        if doi:
            durl = 'https://iopscience.iop.org/article/{0}/pdf'.format(doi)
            self.logger.debug("doc url = %s" % durl)
            return durl

    def _get_article_id(self):
        """Get article's id for IOP
        :returns: Article id
        """
        doi = self.get_doi()
        if doi:
            articleId = doi.replace('10.1088/', '')
            self.logger.debug("articleId = %s" % articleId)
            return articleId

    def get_bibtex_url(self):
        aid = self._get_article_id()
        if aid:
            url = "{0}{1}{2}".format(
                "http://iopscience.iop.org/export?aid=",
                aid,
                "&exportFormat=iopexport_bib&exportType=abs"
                "&navsubmit=Export%2Babstract"
            )
            self.logger.debug("bibtex url = %s" % url)
            return url

    def get_data(self):
        data = dict()
        soup = self._get_soup()
        data.update(papis.downloaders.base.parse_meta_headers(soup))
        abstract_nodes = soup.find_all(
                'div', attrs={'class': 'wd-jnl-art-abstract'})
        if abstract_nodes:
            data['abstract'] = ' '.join(a.text for a in abstract_nodes)
        return data
