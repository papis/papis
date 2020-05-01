import re
import papis.downloaders.base
from typing import Dict, Any, Optional


class Downloader(papis.downloaders.Downloader):

    def __init__(self, url: str):
        papis.downloaders.Downloader.__init__(self,
                                              url,
                                              name="iopscience")
        self.expected_document_extension = 'pdf'
        self.priority = 10

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        url = re.sub(r'/pdf', '', url)
        if re.match(r".*iopscience\.iop\.org.*", url):
            return Downloader(url)
        else:
            return None

    def get_doi(self) -> Optional[str]:
        return self.ctx.data.get('doi')

    def get_document_url(self) -> Optional[str]:
        if 'pdf_url' in self.ctx.data:
            return self.ctx.data.get('pdf_url')
        doi = self.get_doi()
        if doi:
            durl = 'https://iopscience.iop.org/article/{0}/pdf'.format(doi)
            self.logger.debug("doc url = %s" % durl)
            return durl
        else:
            return None

    def _get_article_id(self) -> Optional[str]:
        """Get article's id for IOP
        :returns: Article id
        """
        doi = self.get_doi()
        if doi:
            article_id = doi.replace('10.1088/', '')
            self.logger.debug("article_id = %s" % article_id)
            return article_id
        else:
            return None

    def get_bibtex_url(self) -> Optional[str]:
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
        else:
            return None

    def get_data(self) -> Dict[str, Any]:
        data = dict()
        soup = self._get_soup()
        data.update(papis.downloaders.base.parse_meta_headers(soup))
        abstract_nodes = soup.find_all(
                'div', attrs={'class': 'wd-jnl-art-abstract'})
        if abstract_nodes:
            data['abstract'] = ' '.join(a.text for a in abstract_nodes)
        return data
