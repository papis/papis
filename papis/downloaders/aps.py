import re

import papis.downloaders.fallback


class Downloader(papis.downloaders.fallback.Downloader):
    """Retrieve documents from `APS <https://aps.org>`__"""

    def __init__(self, url: str) -> None:
        super().__init__(
            url, name="aps",
            expected_document_extension="pdf",
            priority=10,
            )

    @classmethod
    def match(cls, url: str) -> papis.downloaders.fallback.Downloader | None:
        return Downloader(url) if re.match(r".*aps.org.*", url) else None

    def get_bibtex_url(self) -> str | None:
        url = "{}?type=bibtex&download=true".format(
            self.uri.replace("/abstract", "/export"))
        self.logger.debug("Using BibTeX URL '%s'.", url)

        return url

    def get_document_url(self) -> str | None:
        url = self.uri.replace("/abstract", "/pdf")
        self.logger.debug("Using document URL: '%s'.", url)

        return url
