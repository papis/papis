import re
from typing import Optional

import papis.downloaders.fallback


class Downloader(papis.downloaders.fallback.Downloader):

    def __init__(self, url: str):
        super.__init__(
            url, "aps",
            expected_document_extension="pdf",
            priority=10,
            )

    @classmethod
    def match(
            cls, url: str) -> Optional[papis.downloaders.fallback.Downloader]:
        return Downloader(url) if re.match(r".*aps.org.*", url) else None

    def get_bibtex_url(self) -> Optional[str]:
        burl = "{}?{}".format(
            re.sub(r"/abstract", r"/export", self.uri),
            "type=bibtex&download=true")
        self.logger.debug("bibtex url = '%s'", burl)
        return burl
