from __future__ import annotations

import os
import re
from functools import cache
from typing import TYPE_CHECKING, Any, ClassVar

from papis.downloaders import Downloader

if TYPE_CHECKING:
    import papis.document


@cache
def _get_citeseerx_key_conversions() -> list[papis.document.KeyConversionPair]:
    from papis.document import EmptyKeyConversion, KeyConversionPair, split_authors_name

    return [
        KeyConversionPair("title", [EmptyKeyConversion]),
        KeyConversionPair("abstract", [EmptyKeyConversion]),
        KeyConversionPair("journal", [EmptyKeyConversion]),
        KeyConversionPair("urls", [EmptyKeyConversion]),
        KeyConversionPair("year", [EmptyKeyConversion]),
        KeyConversionPair("publisher", [EmptyKeyConversion]),
        KeyConversionPair("authors", [
            {"key": "author_list", "action": split_authors_name},
        ])
    ]


class CiteSeerXDownloader(Downloader):
    """Retrieve documents from `CiteSeerX <https://citeseerx.ist.psu.edu>`__"""  # spell: disable

    # NOTE: not sure if this API is open for the public, but it seems to work
    API_URL: ClassVar[str] = "https://citeseerx.ist.psu.edu/api/paper"

    # NOTE: this seems to fail with an 'Internal Server Error 500' more often
    # than not, so it may not be worth it to keep around until it stabilizes
    DOCUMENT_URL: ClassVar[str] = (
        "https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi={pid}"
        )

    def __init__(self, url: str) -> None:
        super().__init__(
            url, "citeseerx",
            expected_document_extension="pdf",
            priority=10,
            )

        self.pid = os.path.basename(url)

    @classmethod
    def match(cls,
              url: str) -> Downloader | None:
        return (CiteSeerXDownloader(url)
                if re.match(r".*citeseerx\.ist\.psu\.edu.*", url)  # spell: disable
                else None)

    def _get_raw_data(self) -> bytes:
        response = self.session.get(
            self.API_URL,
            params={"paper_id": self.pid},
            headers={"token": "undefined", "referer": self.uri},
            )

        if not response.ok:
            self.logger.error("Could not obtain CiteSeerX data: '%s'.", response.reason)

        return response.content

    def get_data(self) -> dict[str, Any]:
        import json
        data = json.loads(self._get_raw_data().decode())

        if "paper" in data:
            from papis.document import keyconversion_to_data
            return keyconversion_to_data(
                _get_citeseerx_key_conversions(), data["paper"])
        else:
            return {}

    def get_document_url(self) -> str | None:
        return self.DOCUMENT_URL.format(pid=self.pid)
