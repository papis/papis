"""The search flow of the source-handler system.

Searching returns all documents that match a given query.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import papis.logging
from papis.sources.dispatch import SourceResult, attempt, resolve_handlers

if TYPE_CHECKING:
    from collections.abc import Sequence

    from papis.document import DocumentLike
    from papis.sources.handler import SearchInput, SourceHandler

logger = papis.logging.get_logger(__name__)

#: Default maximum number of results requested from a single source.
DEFAULT_MAX_RESULTS = 30


@dataclass
class SearchResult(SourceResult):
    """The search flow's outcome for a single handler.

    :param documents: the documents the handler answered with.
    """

    documents: list[DocumentLike] = field(default_factory=list)


def run_handler(
    handler: type[SourceHandler],
    query: SearchInput,
    *,
    max_results: int,
) -> SearchResult:
    """Search one source handler and build its result record.

    :param handler: the handler to run.
    :param query: the query to search with.
    :param max_results: maximum number of results for this handler.
    :returns: the outcome search result.
    """
    if "search" not in handler.capabilities:
        return SearchResult(
            source=handler.name,
            priority=handler.priority,
            status="no_match",
            message="source does not support search",
        )

    unsupported_fields = sorted(
        name
        for name, values in query.filters.items()
        if values and name not in handler.search_fields
    )
    if unsupported_fields:
        supported_fields = ", ".join(handler.search_fields) or "free-text only"
        return SearchResult(
            source=handler.name,
            priority=handler.priority,
            status="no_match",
            message=(
                f"cannot use filter(s): {', '.join(unsupported_fields)} "
                f"(supports: {supported_fields})"
            ),
        )

    output, error = attempt(
        handler.name,
        handler.search,
        query,
        max_results=max_results,
    )

    if error is not None or output is None:
        return SearchResult(
            source=handler.name,
            priority=handler.priority,
            status="failed",
            message=error,
        )

    return SearchResult(
        source=handler.name,
        priority=handler.priority,
        status="ok" if output.documents else "no_result",
        documents=output.documents,
        message=output.message,
    )


def search(
    query: SearchInput,
    *,
    sources: Sequence[str] | None = None,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> list[SearchResult]:
    """Search the sources with *query*.

    A source handler that cannot process every provided filter is not run at all
    and reports ``"no_match"``. This is because dropping filters silently is likely
    to lead to useless results.

    :param query: the query to search with.
    :param sources: constrain search to these source handlers.
    :param max_results: maximum number of results per source.
    :raises ValueError: if *query* is empty or *sources* contains an unknown handler.
    """
    if not (query.input or any(query.filters.values())):
        raise ValueError("search requires a query or at least one filter")

    return [
        run_handler(handler, query, max_results=max_results)
        for handler in resolve_handlers(sources, capability="search")
    ]
