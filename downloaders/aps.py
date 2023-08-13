import re
from typing import Optional

import papis.downloaders.fallback


class Downloader(papis.downloaders.fallback.Downloader):

    def __init__(self, url: str) -> None:
        super().__init__(
            url, name="aps",
            expected_document_extension="pdf",
            priority=10,
            )

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.fallback.Downloader]:
        return Downloader(url) if re.match(r".*aps.org.*", url) else None

    def get_bibtex_url(self) -> Optional[str]:
        url = "{}?type=bibtex&download=true".format(
            self.uri.replace("/abstract", "/export"))
        self.logger.debug("Using BibTeX URL '%s'.", url)

        return url

    def get_document_url(self) -> Optional[str]:
        url = self.uri.replace("/abstract", "/pdf")
        self.logger.debug("Using document URL: '%s'.", url)

        return url
