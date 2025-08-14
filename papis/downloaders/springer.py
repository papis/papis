import re
from typing import Any, ClassVar

import papis.document
import papis.downloaders.base


class Downloader(papis.downloaders.Downloader):
    """Retrieve documents from `SpringerLink <https://link.springer.com>`__"""

    DOCUMENT_URL: ClassVar[str] = (
        "https://link.springer.com/content/pdf/{doi}.pdf"
        )

    BIBTEX_URL: ClassVar[str] = (
        "https://citation-needed.springer.com/v2/"
        "references/{doi}?format=bibtex&amp;flavour=citation"
        )

    def __init__(self, url: str) -> None:
        super().__init__(
            url, name="springer",
            expected_document_extension="pdf",
            priority=10,
            )

    @classmethod
    def match(cls, url: str) -> papis.downloaders.Downloader | None:
        return Downloader(url) if re.match(r".*link\.springer.com.*", url) else None

    def get_data(self) -> dict[str, Any]:
        soup = self._get_soup()
        data = papis.downloaders.base.parse_meta_headers(soup)

        if "publication_date" in data:
            dates = data["publication_date"].split("/")
            data["year"] = dates[0]

        return data

    def get_bibtex_url(self) -> str | None:
        if "doi" in self.ctx.data:
            url = self.BIBTEX_URL.format(doi=self.ctx.data["doi"])
            self.logger.debug("Using BibTeX URL: '%s'.", url)
            return url
        else:
            return None

    def get_document_url(self) -> str | None:
        if "doi" in self.ctx.data:
            url = self.DOCUMENT_URL.format(doi=self.ctx.data["doi"])
            self.logger.debug("Using document URL: '%s'.", url)
            return url
        else:
            return None
