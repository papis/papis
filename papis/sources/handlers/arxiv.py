"""arXiv source handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

import papis.arxiv
import papis.config
from papis.sources.handler import (
    FileReference,
    LookupOutput,
    SearchOutput,
    SourceHandler,
)

if TYPE_CHECKING:
    from papis.sources.handler import LookupInput, SearchInput


class ArxivHandler(SourceHandler):
    """Retrieve documents from arXiv <https://arxiv.org>."""

    name = "arxiv"
    search_fields = (
        "author",
        "title",
        "abstract",
        "comment",
        "journal",
        "report_number",
        "category",
        "eprint",
        "arxivid",
    )

    def __init__(self, arxivid: str) -> None:
        super().__init__()
        self.arxivid = arxivid

    @classmethod
    def match_for_lookup(cls, evidence: LookupInput) -> ArxivHandler | None:
        eprinttype = evidence.fields.get("eprinttype", "").lower()
        if not eprinttype or eprinttype == "arxiv":
            arxivid = papis.arxiv.find_arxivid_in_text(
                evidence.fields.get("eprint", "")
            )
            if arxivid:
                return cls(arxivid)

        arxivid = papis.arxiv.find_arxivid_in_text(evidence.fields.get("arxivid", ""))
        if arxivid:
            return cls(arxivid)

        arxivid = papis.arxiv.find_arxivid_in_text(evidence.input)
        return cls(arxivid) if arxivid else None

    def lookup(self, evidence: LookupInput) -> LookupOutput:
        documents = papis.arxiv.get_data(id_list=self.arxivid, max_results=1)
        document = documents[0] if documents else None

        files: list[FileReference] = []
        if document is not None:
            doc_url = document.get(papis.config.getstring("doc-url-key-name"))
            if doc_url:
                files = [FileReference(url=doc_url, extension="pdf")]

        return LookupOutput(
            document=document,
            files=files,
        )

    @classmethod
    def search(cls, query: SearchInput, *, max_results: int) -> SearchOutput:
        documents = papis.arxiv.get_data(
            query=query.input,
            author=query.filters.get("author", []),
            title=query.filters.get("title", []),
            abstract=query.filters.get("abstract", []),
            comment=query.filters.get("comment", []),
            journal=query.filters.get("journal", []),
            report_number=query.filters.get("report_number", []),
            category=query.filters.get("category", []),
            # FIXME: We don't check whether the 'eprint' has the right 'eprinttype'.
            # This works for now because searches are always called with an explicit
            # source handler.
            id_list=(
                query.filters.get("eprint", []) + query.filters.get("arxivid", [])
            ),
            max_results=max_results,
        )

        return SearchOutput(documents=documents)
