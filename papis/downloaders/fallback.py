import doi
import papis.downloaders.base
import bs4


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url, name="fallback"):
        papis.downloaders.base.Downloader.__init__(self, url, name=name)
        self.priority = -1

    @classmethod
    def match(cls, url):
        return Downloader(url)

    def get_data(self):
        data = dict()
        body = self._get_body()
        soup = bs4.BeautifulSoup(body, "html.parser")
        data.update(papis.downloaders.base.parse_meta_headers(soup))
        return data

    def get_doi(self):
        if 'doi' in self.ctx.data:
            return self.ctx.data['doi']
        body = self.session.get(self.uri).content.decode('utf-8')
        self.logger.info('trying to parse doi...')
        return doi.find_doi_in_text(body)

    def get_document_url(self):
        if 'pdf_url' in self.ctx.data:
            url = self.ctx.data.get('pdf_url')
            self.logger.debug("got a pdf url = %s" % url)
            return url
