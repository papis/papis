"""PubMed source handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

import papis.pubmed
from papis.sources.handler import LookupOutput, SourceHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput


class PmidHandler(SourceHandler):
    """Retrieve documents for a PubMed ID (PMID)."""

    name = "pmid"

    def __init__(self, pmid: str) -> None:
        super().__init__()
        self.pmid = pmid

    @classmethod
    def match_for_lookup(cls, evidence: LookupInput) -> PmidHandler | None:
        candidate = evidence.input
        if not candidate.isdigit():
            return None

        # NOTE: a 978/979 ISBN-13 is never a PMID, so don't query PubMed for it.
        if len(candidate) == 13 and candidate.startswith(("978", "979")):
            return None

        return cls(candidate)

    def lookup(self, evidence: LookupInput) -> LookupOutput:
        data = papis.pubmed.get_data(self.pmid)

        return LookupOutput(
            document=data if data else None,
        )
