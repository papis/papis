import re
from typing import Any, ClassVar, Dict, Optional

import papis.document
import papis.downloaders


class Downloader(papis.downloaders.Downloader):
    DOCUMENT_URL = (
        "https://pubs.acs.org/doi/pdf/{doi}"
        )   # type: ClassVar[str]

    BIBTEX_URL = (
        "https://pubs.acs.org/action/downloadCitation"
        "?format=bibtex&cookieSet=1&doi={doi}"
        )   # type: ClassVar[str]

    def __init__(self, url: str) -> None:
        super().__init__(
            url, "acs",
            expected_document_extension="pdf",
            cookies={"gdpr": "true"},
            priority=10,
            )

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        return Downloader(url) if re.match(r".*acs.org.*", url) else None

    def get_data(self) -> Dict[str, Any]:
        soup = self._get_soup()
        data = papis.downloaders.base.parse_meta_headers(soup)

        return data

    def get_document_url(self) -> Optional[str]:
        doi = self.ctx.data.get("doi")
        if doi is not None:
            return self.DOCUMENT_URL.format(doi=doi)

        return None

    def get_bibtex_url(self) -> Optional[str]:
        doi = self.ctx.data.get("doi")
        if doi is not None:
            url = self.BIBTEX_URL.format(doi=doi)
            self.logger.debug("Using BibTeX URL: '%s'.", url)
            return url

        return None
