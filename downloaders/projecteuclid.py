import re
from typing import Optional

import papis.downloaders.fallback


class Downloader(papis.downloaders.fallback.Downloader):
    _BIBTEX_URL = "https://projecteuclid.org/citation/download/citation-{}.bib"

    def __init__(self, url: str) -> None:
        super().__init__(
            uri=url, name="projecteuclid",
            expected_document_extension="pdf",
            priority=10,
            )

    @classmethod
    def match(cls, url: str) -> Optional["Downloader"]:
        if re.match(r".*projecteuclid\.org.*", url):
            return Downloader(url)
        else:
            return None

    def get_bibtex_url(self) -> Optional[str]:
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
