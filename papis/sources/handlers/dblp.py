"""DBLP source handler."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import papis.dblp
from papis.exceptions import SourceError
from papis.sources.handler import LookupOutput, SearchOutput, SourceHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput, SearchInput

#: DBLP key pattern: ``<venue type>/<venue id>/<document id>`` plus an optional extra
#: component.
_KEY_RE = re.compile(r"^[^/]+/[^/]+/.+$")

#: Shapes that pass the key pattern but are never DBLP keys, e.g. DOIs and absolute URLs
_NON_KEY_RE = re.compile(r"(?:^10\.\d+/|://)")

#: Pattern for DBLP record page URLs, e.g. ``https://dblp.org/rec/conf/iccg/x.html``.
_URL_RE = re.compile(r"^https?://dblp\.org/rec/(?P<key>.+?)\.html(?:[?#].*)?$")


class DblpHandler(SourceHandler):
    """Retrieve documents from DBLP <https://dblp.org>."""

    name = "dblp"

    def __init__(self, dblp_key: str) -> None:
        super().__init__()
        self.dblp_key = dblp_key

    @classmethod
    def match_for_lookup(cls, evidence: LookupInput) -> DblpHandler | None:
        text = evidence.input

        m = _URL_RE.match(text)
        if m is not None:
            return cls(m.group("key"))

        if _KEY_RE.match(text) and not _NON_KEY_RE.search(text):
            return cls(text)

        return None

    def lookup(self, evidence: LookupInput) -> LookupOutput:
        from requests.exceptions import RequestException

        from papis.bibtex import bibtex_to_dict
        from papis.utils import get_session

        bib_url = papis.dblp.DBLP_BIB_FORMAT.format(uri=self.dblp_key)
        try:
            with get_session() as session:
                response = session.get(bib_url)
        except RequestException as exc:
            raise SourceError(f"Could not query DBLP: {exc}") from exc

        if response.status_code in {404, 410}:
            # NOTE: absence means no record found
            return LookupOutput()

        if not response.ok:
            raise SourceError(f"Could not query DBLP: HTTP {response.status_code}")

        entries = bibtex_to_dict(response.content.decode())
        if not entries:
            raise SourceError("Unexpected response from DBLP: not valid BibTeX")

        message = None
        if len(entries) > 1:
            message = (
                f"Found {len(entries)} BibTeX entries for '{self.dblp_key}'. "
                "Picking the first one."
            )

        return LookupOutput(
            document=entries[0],
            message=message,
        )

    @classmethod
    def search(cls, query: SearchInput, *, max_results: int) -> SearchOutput:
        documents = papis.dblp.get_data(query=query.input, max_results=max_results)

        return SearchOutput(
            documents=documents,
        )
