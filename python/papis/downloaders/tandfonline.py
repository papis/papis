from __future__ import annotations

import re
from typing import Any, ClassVar

from papis.downloaders import Downloader

tf_to_bibtex_converter = {
    # FIXME: what other types are there?
    "research-article": "article",
}   # Dict[str, str]


def _parse_year(date: str) -> int | None:
    from datetime import datetime
    try:
        return datetime.strptime(date, "%d %b %Y").year
    except ValueError:
        return None


def _parse_month(date: str) -> int | None:
    from datetime import datetime
    try:
        return datetime.strptime(date, "%d %b %Y").month
    except ValueError:
        return None


class TaylorFrancisDownloader(Downloader):
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
    def match(cls, url: str) -> Downloader | None:
        return (TaylorFrancisDownloader(url)
                if re.match(r".*tandfonline.com.*", url) else None)

    def get_data(self) -> dict[str, Any]:
        from papis.downloaders.base import parse_meta_headers
        soup = self._get_soup()
        data = parse_meta_headers(soup)

        from papis.document import KeyConversionPair, keyconversion_to_data
        article_key_conversion = [
            KeyConversionPair("type", [
                {"key": None, "action": lambda x: tf_to_bibtex_converter.get(x, x)}
            ]),
            KeyConversionPair("date", [
                {"key": "year", "action": _parse_year},
                {"key": "month", "action": _parse_month},
            ])
        ]

        data = keyconversion_to_data(
            article_key_conversion, data, keep_unknown_keys=True)

        if "doi" not in data and "doi" in self.uri:
            data["doi"] = self.uri[len(self.BASE_URL) + 1:]

        return data

    def get_bibtex_url(self) -> str | None:
        doi = self.ctx.data.get("doi")
        if doi is None:
            return None

        url = self.BIBTEX_URL.format(doi=doi)
        self.logger.debug("Using BibTeX URL: '%s'.", url)
        return url

    def get_document_url(self) -> str | None:
        doi = self.ctx.data.get("doi")
        if doi is None:
            return None

        url = self.DOCUMENT_URL.format(doi=doi)
        self.logger.debug("Using document URL: '%s'.", url)
        return url
