import re
from typing import Optional

import papis.downloaders.fallback


class Downloader(papis.downloaders.fallback.Downloader):

    def __init__(self, url: str):
        super().__init__(
            url, name="hal",
            expected_document_extension="pdf",
            priority=10,
            )

    @classmethod
    def match(
            cls, url: str) -> Optional[papis.downloaders.fallback.Downloader]:
        if re.match(r".*hal\.archives-ouvertes\.fr.*", url):
            return Downloader(url)
        else:
            return None

    def get_bibtex_url(self) -> Optional[str]:
        if "pdf_url" in self.ctx.data:
            url = re.sub(r"document", "bibtex", self.uri)
            self.logger.debug("bibtex url = '%s'", url)
            return url
        else:
            return None
