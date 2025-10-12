from __future__ import annotations

import re

from papis.downloaders import Downloader
from papis.downloaders.fallback import FallbackDownloader


class APSDownloader(FallbackDownloader):
    """Retrieve documents from `APS <https://aps.org>`__"""

    def __init__(self, url: str) -> None:
        super().__init__(
            url, name="aps",
            expected_document_extension="pdf",
            priority=10,
            )

    @classmethod
    def match(cls, url: str) -> Downloader | None:
        return APSDownloader(url) if re.match(r".*aps.org.*", url) else None

    def get_bibtex_url(self) -> str | None:
        url = "{}?type=bibtex&download=true".format(
            self.uri.replace("/abstract", "/export"))
        self.logger.debug("Using BibTeX URL '%s'.", url)

        return url

    def get_document_url(self) -> str | None:
        url = self.uri.replace("/abstract", "/pdf")
        self.logger.debug("Using document URL: '%s'.", url)

        return url
