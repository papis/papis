import doi
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(self, url, name="fallback")
        self.priority = -1

    @classmethod
    def match(cls, url):
        return Downloader(url)

    def get_doi(self):
        body = self.session.get(self.uri).content.decode('utf-8')
        self.logger.info('trying to parse doi...')
        return doi.find_doi_in_text(body)
