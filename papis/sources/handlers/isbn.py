"""ISBN source handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

import papis.isbn
from papis.sources.handler import LookupOutput, SearchOutput, SourceHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput, SearchInput


class IsbnHandler(SourceHandler):
    """Retrieve documents for an ISBN."""

    name = "isbn"

    def __init__(self, isbn: str) -> None:
        super().__init__()
        self.isbn = isbn

    @classmethod
    def match_for_lookup(cls, evidence: LookupInput) -> IsbnHandler | None:
        from papis.isbn import notisbn, strip_isbnlike

        candidate = strip_isbnlike(evidence.input)
        if notisbn(candidate):
            return None

        return cls(candidate)

    def lookup(self, evidence: LookupInput) -> LookupOutput:
        documents = papis.isbn.get_data(isbn_like=self.isbn)
        return LookupOutput(
            document=documents[0] if documents else None,
        )

    @classmethod
    def search(cls, query: SearchInput, *, max_results: int) -> SearchOutput:
        documents = papis.isbn.get_data(query=query.input)

        return SearchOutput(
            documents=documents[:max_results],
        )
