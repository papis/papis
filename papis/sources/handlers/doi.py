"""DOI source handler."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import papis.config
import papis.crossref
from papis.sources.handler import FileReference, LookupOutput, SourceHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


class DoiHandler(SourceHandler):
    """Retrieve documents for a DOI."""

    name = "doi"
    priority = 6

    def __init__(self, doi: str) -> None:
        super().__init__()
        self.doi = doi

    @classmethod
    def match_for_lookup(cls, evidence: LookupInput) -> DoiHandler | None:
        doi = evidence.fields.get("doi", "")
        found = papis.crossref.find_doi(doi) if doi else None
        if not found:
            found = papis.crossref.find_doi(evidence.input)

        return cls(found.lower()) if found else None

    def lookup(self, evidence: LookupInput) -> LookupOutput:
        documents: list[dict[str, Any]] = []
        try:
            documents = [papis.crossref.doi_to_data(self.doi)]
        except ValueError as exc:
            # NOTE: ValueError means no data could be found, so we return nothing, which
            # will result in a status of `no_result`.
            self.logger.debug("Could not retrieve data for DOI '%s': %s", self.doi, exc)

        document = documents[0] if documents else None

        files: list[FileReference] = []
        if document is not None:
            doc_url = document.get(papis.config.getstring("doc-url-key-name"))
            if doc_url:
                files = [FileReference(url=doc_url)]

        return LookupOutput(
            document=document,
            files=files,
        )
