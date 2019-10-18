import doi
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url, name="fallback"):
        papis.downloaders.base.Downloader.__init__(self, url, name=name)
        self.priority = -1

    @classmethod
    def match(cls, url):
        return Downloader(url)

    def get_data(self):
        data = dict()
        soup = self._get_soup()
        data.update(papis.downloaders.base.parse_meta_headers(soup))
        return data

    def get_doi(self):
        if 'doi' in self.ctx.data:
            return self.ctx.data['doi']
        soup = self._get_soup()
        self.logger.info('trying to parse doi...')
        return doi.find_doi_in_text(str(soup))

    def get_document_url(self):
        if 'pdf_url' in self.ctx.data:
            url = self.ctx.data.get('pdf_url')
            self.logger.debug("got a pdf url = %s" % url)
            return url
