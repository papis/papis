import re
from typing import Any, ClassVar, Dict, Optional

import papis.downloaders.base
import papis.document


class Downloader(papis.downloaders.Downloader):
    DOCUMENT_URL = (
        "https://link.springer.com/content/pdf/{doi}.pdf"
        )   # type: ClassVar[str]

    BIBTEX_URL = (
        "https://citation-needed.springer.com/v2/"
        "references/{doi}?format=bibtex&amp;flavour=citation"
        )   # type: ClassVar[str]

    def __init__(self, url: str) -> None:
        super().__init__(
            url, name="springer",
            expected_document_extension="pdf",
            priority=10,
            )

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        return Downloader(url) if re.match(r".*link\.springer.com.*", url) else None

    def get_data(self) -> Dict[str, Any]:
        soup = self._get_soup()
        data = papis.downloaders.base.parse_meta_headers(soup)

        if "publication_date" in data:
            dates = data["publication_date"].split("/")
            data["year"] = dates[0]

        return data

    def get_bibtex_url(self) -> Optional[str]:
        if "doi" in self.ctx.data:
            url = self.BIBTEX_URL.format(doi=self.ctx.data["doi"])
            self.logger.debug("Using BibTeX URL: '%s'.", url)
            return url
        else:
            return None

    def get_document_url(self) -> Optional[str]:
        if "doi" in self.ctx.data:
            url = self.DOCUMENT_URL.format(doi=self.ctx.data["doi"])
            self.logger.debug("Using document URL: '%s'.", url)
            return url
        else:
            return None
