import os
import re
from typing import Any, ClassVar, Dict, Optional

import papis.utils
import papis.document
import papis.downloaders

_K = papis.document.KeyConversionPair
article_key_conversion = [
    _K("title", [papis.document.EmptyKeyConversion]),
    _K("abstract", [papis.document.EmptyKeyConversion]),
    _K("journal", [papis.document.EmptyKeyConversion]),
    _K("urls", [papis.document.EmptyKeyConversion]),
    _K("year", [papis.document.EmptyKeyConversion]),
    _K("publisher", [papis.document.EmptyKeyConversion]),
    _K("authors", [
        {"key": "author_list", "action": papis.document.split_authors_name},
    ])
]


class Downloader(papis.downloaders.Downloader):
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
              url: str) -> Optional[papis.downloaders.Downloader]:
        return (Downloader(url)
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

    def get_data(self) -> Dict[str, Any]:
        import json
        data = json.loads(self._get_raw_data().decode())

        if "paper" in data:
            return papis.document.keyconversion_to_data(
                article_key_conversion, data["paper"])
        else:
            return {}

    def get_document_url(self) -> Optional[str]:
        return self.DOCUMENT_URL.format(pid=self.pid)
