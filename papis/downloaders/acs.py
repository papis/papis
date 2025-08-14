import re
from typing import Any, ClassVar

import papis.document
import papis.downloaders


class Downloader(papis.downloaders.Downloader):
    """Retrieve documents from `ACS Publications <https://pubs.acs.org>`__"""

    DOCUMENT_URL: ClassVar[str] = (
        "https://pubs.acs.org/doi/pdf/{doi}"
        )

    BIBTEX_URL: ClassVar[str] = (
        "https://pubs.acs.org/action/downloadCitation"
        "?format=bibtex&cookieSet=1&doi={doi}"
        )

    def __init__(self, url: str) -> None:
        super().__init__(
            url, "acs",
            expected_document_extension="pdf",
            cookies={"gdpr": "true"},
            priority=10,
            )

    @classmethod
    def match(cls, url: str) -> papis.downloaders.Downloader | None:
        return Downloader(url) if re.match(r".*acs.org.*", url) else None

    def get_data(self) -> dict[str, Any]:
        soup = self._get_soup()
        data = papis.downloaders.base.parse_meta_headers(soup)

        return data

    def get_document_url(self) -> str | None:
        doi = self.ctx.data.get("doi")
        if doi is not None:
            return self.DOCUMENT_URL.format(doi=doi)

        return None

    def get_bibtex_url(self) -> str | None:
        doi = self.ctx.data.get("doi")
        if doi is not None:
            url = self.BIBTEX_URL.format(doi=doi)
            self.logger.debug("Using BibTeX URL: '%s'.", url)
            return url

        return None
