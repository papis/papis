import doi
import papis.downloaders.base

from typing import Dict, Any, List, Optional


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, uri: str, name: str = "fallback"):
        papis.downloaders.base.Downloader.__init__(
            self, uri=uri, name=name)
        self.priority = -1

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.base.Downloader]:
        return Downloader(url)

    def get_data(self) -> Dict[str, Any]:
        data = dict()
        soup = self._get_soup()
        data.update(papis.downloaders.base.parse_meta_headers(soup))
        return data

    def get_doi(self) -> Optional[str]:
        if self.ctx.data and 'doi' in self.ctx.data:
            _doi = self.ctx.data['doi']
            return str(_doi) if _doi else None
        soup = self._get_soup()
        self.logger.info('trying to parse doi from url body...')
        if soup:
            return doi.find_doi_in_text(str(soup))
        else:
            return None

    def get_document_url(self) -> Optional[str]:
        if 'pdf_url' in self.ctx.data:
            url = self.ctx.data.get('pdf_url')
            self.logger.debug("got a pdf url = %s" % url)
            return url
        else:
            return None
