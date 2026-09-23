"""Crossref source handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

import papis.crossref
from papis.exceptions import SourceError
from papis.sources.handler import LookupOutput, SearchOutput, SourceHandler

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput, SearchInput


class CrossrefHandler(SourceHandler):
    """Retrieve documents from Crossref <https://www.crossref.org>."""

    name = "crossref"
    search_fields = (
        "author",
        "title",
        "type",
        "journal",
        "year",
        "doi",
        "isbn",
        "issn",
    )

    def __init__(self, title: str) -> None:
        super().__init__()
        self.title = title

    @classmethod
    def match_for_lookup(cls, evidence: LookupInput) -> CrossrefHandler | None:
        title = evidence.fields.get("title", "")
        return cls(title) if title else None

    def lookup(self, evidence: LookupInput) -> LookupOutput:
        documents = papis.crossref.get_data(title=self.title)

        message = None
        if len(documents) > 1:
            message = (
                f"Title query '{self.title}' returned {len(documents)} results. "
                "Picking the first one."
            )
            documents = documents[:1]

        return LookupOutput(
            document=documents[0] if documents else None,
            message=message,
        )

    @classmethod
    def search(cls, query: SearchInput, *, max_results: int) -> SearchOutput:
        filters: dict[str, list[str]] = {}

        types: list[str] = []
        for value in query.filters.get("type", []):
            crossref_type = papis.crossref.BIBTEX_TO_CROSSREF_CONVERTER.get(
                value, value
            )
            # NOTE: since we pass through types that aren't in our conversion table, we
            # check if they are valid Crossref types.
            if crossref_type not in papis.crossref.CROSSREF_TYPES:
                raise SourceError(f"cannot search Crossref for type '{value}'")
            types.append(crossref_type)

        for name, values in [
            ("type", types),
            ("container-title", query.filters.get("journal", [])),
            ("isbn", query.filters.get("isbn", [])),
            ("issn", query.filters.get("issn", [])),
        ]:
            if values:
                filters[name] = values

        # NOTE: Crossref can't handle multiple explicitly set years in one request, so
        # we turn supplied years into a range.
        years = sorted(query.filters.get("year", []))
        if years:
            filters["from-pub-date"] = [years[0]]
            filters["until-pub-date"] = [years[-1]]

        documents = papis.crossref.get_data(
            # NOTE: Crossref will search for all words in field queries in the relevant
            # fields. So we just join values for `author` and `title` queries.
            # See <https://github.com/CrossRef/rest-api-doc#field-queries>.
            query=query.input,
            author=" ".join(query.filters.get("author", [])),
            title=" ".join(query.filters.get("title", [])),
            dois=query.filters.get("doi", []),
            max_results=max_results,
            filters=filters,
        )

        return SearchOutput(documents=documents)
