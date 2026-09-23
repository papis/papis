"""NBER source handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from papis.sources.handlers.web import WebsiteHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


_BIBTEX_URL = "https://back.nber.org/bibliographic/{0}.bib"
_FILE_URL = "https://www.nber.org/system/files/working_papers/{0}/{0}.pdf"

#: Match either an NBER working paper URL or a bare working-paper ID.
_URL_RE = re.compile(r"^(?:https?://(?:www\.)?nber\.org/papers/)?(w\d+)(?:[/?#].*)?$")


class NberHandler(WebsiteHandler):
    """Retrieve documents from `NBER <https://www.nber.org>`__.

    Metadata comes via BibTeX URL only.
    """

    name = "nber"
    url_or_id_re = _URL_RE

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:  # ruff: ignore[no-self-use]
        return {}

    def get_file_url(self, evidence: LookupInput) -> str | None:
        return _FILE_URL.format(_extract_nberid(self.url))

    def get_bibtex_url(self, evidence: LookupInput) -> str | None:
        return _BIBTEX_URL.format(_extract_nberid(self.url))


def _extract_nberid(url: str) -> str:
    """Extract the working-paper ID from an NBER URL or bare ID."""
    match = _URL_RE.match(url)
    assert match is not None
    return match.group(1)
