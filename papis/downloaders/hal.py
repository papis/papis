import re
import papis.downloaders.fallback
from typing import Optional


class Downloader(papis.downloaders.fallback.Downloader):

    def __init__(self, url: str):
        papis.downloaders.fallback.Downloader.__init__(self, url, name="hal")
        self.expected_document_extension = 'pdf'
        self.priority = 10

    @classmethod
    def match(
            cls, url: str) -> Optional[papis.downloaders.fallback.Downloader]:
        if re.match(r".*hal\.archives-ouvertes\.fr.*", url):
            return Downloader(url)
        else:
            return None

    def get_bibtex_url(self) -> Optional[str]:
        if 'pdf_url' in self.ctx.data:
            url = re.sub(r'document', 'bibtex', self.uri)
            self.logger.debug('bibtex url = {url}'.format(url=url))
            return url
        else:
            return None
