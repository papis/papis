from __future__ import annotations

import re
from typing import TYPE_CHECKING

from papis.downloaders.fallback import FallbackDownloader

if TYPE_CHECKING:
    from papis.downloaders import Downloader


class ProjectEuclidDownloader(FallbackDownloader):
    """Retrieve documents from `Project Euclid <https://projecteuclid.org>`__"""

    _BIBTEX_URL = "https://projecteuclid.org/citation/download/citation-{}.bib"

    def __init__(self, url: str) -> None:
        super().__init__(
            uri=url, name="projecteuclid",
            expected_document_extension="pdf",
            priority=10,
            )

    @classmethod
    def match(cls, url: str) -> Downloader | None:
        if re.match(r".*projecteuclid\.org.*", url):
            return ProjectEuclidDownloader(url)
        else:
            return None

    def get_bibtex_url(self) -> str | None:
        try:
            # NOTE: this was determined heuristically by looking at the IDs
            # generated for a couple of papers and may change in the future
            identifier = "{}{}_{}".format(
                self.ctx.data["journal_abbrev"],
                self.ctx.data["volume"],
                self.ctx.data["firstpage"])

            return self._BIBTEX_URL.format(identifier)
        except KeyError:
            return None
