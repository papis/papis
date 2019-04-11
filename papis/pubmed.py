import papis.importer
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(
            self, uri=url, name="pubmed")

    def get_bibtex_url(self):
        return (
            "http://pubmed.macropus.org/articles/"
            "?format=text%2Fbibtex&id={pmid}"
            .format(pmid=self.uri)
        )


class Importer(papis.importer.Importer):

    """Importer downloading data from a pubmed id"""

    def __init__(self, uri='', **kwargs):
        papis.importer.Importer.__init__(
            self, name='pubmed', uri=uri, **kwargs)
        self.downloader = Downloader(uri)

    @classmethod
    def match(cls, uri):
        # TODO:
        pass

    def fetch(self):
        self.downloader.fetch()
        self.ctx = self.downloader.ctx
