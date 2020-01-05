from typing import Optional

import papis.importer
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url: str):
        papis.downloaders.base.Downloader.__init__(
            self, uri=url, name="pubmed")

    def get_bibtex_url(self) -> Optional[str]:
        return ("http://pubmed.macropus.org/articles/"
                "?format=text%2Fbibtex&id={pmid}"
                .format(pmid=self.uri))


class Importer(papis.importer.Importer):

    """Importer downloading data from a pubmed id"""

    def __init__(self, uri: str = ''):
        papis.importer.Importer.__init__(self, name='pubmed', uri=uri)
        self.downloader = Downloader(uri)

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        # TODO:
        pass

    def fetch(self) -> None:
        self.downloader.fetch()
        self.ctx = self.downloader.ctx
