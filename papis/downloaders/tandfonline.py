import re
from typing import Any, ClassVar, Dict, Optional

import papis.document
import papis.downloaders.base


tf_to_bibtex_converter = {
    # FIXME: what other types are there?
    "research-article": "article",
}   # Dict[str, str]

_K = papis.document.KeyConversionPair
article_key_conversion = [
    _K("type", [{"key": None, "action": lambda x: tf_to_bibtex_converter.get(x, x)}]),
    _K("date", [
        {"key": "year", "action": lambda x: _parse_year(x)},  # noqa: PLW0108
        {"key": "month", "action": lambda x: _parse_month(x)},  # noqa: PLW0108
    ])
]


def _parse_year(date: str) -> Optional[int]:
    from datetime import datetime
    try:
        return datetime.strptime(date, "%d %b %Y").year
    except ValueError:
        return None


def _parse_month(date: str) -> Optional[int]:
    from datetime import datetime
    try:
        return datetime.strptime(date, "%d %b %Y").month
    except ValueError:
        return None


class Downloader(papis.downloaders.Downloader):
    """Retrieve documents from `Taylor & Francis <https://www.tandfonline.com>`__"""

    BASE_URL: ClassVar[str] = "https://www.tandfonline.com/doi/full"

    DOCUMENT_URL: ClassVar[str] = (
        "https://www.tandfonline.com/doi/pdf/{doi}"
        )

    BIBTEX_URL: ClassVar[str] = (
        "https://www.tandfonline.com/action/downloadCitation"
        "?format=bibtex&cookieSet=1&doi={doi}"
        )

    def __init__(self, url: str) -> None:
        super().__init__(
            url, name="tandfonline",
            expected_document_extension="pdf",
            priority=10,
            )

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        return (Downloader(url)
                if re.match(r".*tandfonline.com.*", url) else None)

    def get_data(self) -> Dict[str, Any]:
        soup = self._get_soup()
        data = papis.downloaders.base.parse_meta_headers(soup)

        data = papis.document.keyconversion_to_data(
            article_key_conversion, data, keep_unknown_keys=True)

        if "doi" not in data and "doi" in self.uri:
            data["doi"] = self.uri[len(self.BASE_URL) + 1:]

        return data

    def get_bibtex_url(self) -> Optional[str]:
        doi = self.ctx.data.get("doi")
        if doi is None:
            return None

        url = self.BIBTEX_URL.format(doi=doi)
        self.logger.debug("Using BibTeX URL: '%s'.", url)
        return url

    def get_document_url(self) -> Optional[str]:
        doi = self.ctx.data.get("doi")
        if doi is None:
            return None

        url = self.DOCUMENT_URL.format(doi=doi)
        self.logger.debug("Using document URL: '%s'.", url)
        return url
