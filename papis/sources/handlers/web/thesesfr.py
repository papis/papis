"""theses.fr source handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from papis.sources.handlers.web import WebsiteHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


#: Match either a theses.fr URL or a bare thesis identifier ('nnt' in
#: French). Not specified in the docs, but the pattern all published theses
#: follow until now.
_URL_RE = re.compile(r"^(?:https?://(?:www\.)?theses\.fr/)?(\d{4}[A-Z]{3,5}\d{3,5})")

_FILE_URL = "https://theses.fr/api/v1/document/{id}"
_BIBTEX_URL = "https://www.theses.fr/{id}.bib"


class ThesesFrHandler(WebsiteHandler):
    """Retrieve documents from `theses.fr <https://theses.fr/en/>`__.

    Matches an URL or a bare identifier. All metadata is added via the BibTeX URL.

    API Documentation: https://api.gouv.fr/documentation/scanR
    """

    name = "thesesfr"
    url_or_id_re = _URL_RE

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:  # ruff: ignore[no-self-use]
        return {}

    def get_file_url(self, evidence: LookupInput) -> str | None:
        return _FILE_URL.format(id=_extract_identifier(self.url))

    def get_bibtex_url(self, evidence: LookupInput) -> str | None:
        return _BIBTEX_URL.format(id=_extract_identifier(self.url))


def _extract_identifier(url: str) -> str:
    match = _URL_RE.match(url)
    assert match is not None
    return match.group(1)
