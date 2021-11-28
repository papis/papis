import re
import papis.downloaders.fallback

from typing import Optional


class Downloader(papis.downloaders.fallback.Downloader):

    def __init__(self, url: str):
        papis.downloaders.fallback.Downloader.__init__(
            self,
            uri=url,
            name="aps")
        self.expected_document_extension = 'pdf'
        self.priority = 10

    @classmethod
    def match(
            cls, url: str) -> Optional[papis.downloaders.fallback.Downloader]:
        return Downloader(url) if re.match(r".*aps.org.*", url) else None

    def get_bibtex_url(self) -> Optional[str]:
        burl = "{}?{}".format(
            re.sub(r'/abstract', r'/export', self.uri),
            "type=bibtex&download=true")
        self.logger.debug("bibtex url = '%s'", burl)
        return burl
