from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.exceptions import SourceError
from papis.sources.handler import SearchInput
from papis.sources.search import search
from papis.testing import make_lookup_handler, make_search_handler

if TYPE_CHECKING:
    from typing import Any


def test_fan_out_to_all_searchable(handler_registry: Any) -> None:
    """Without explicit sources, every handler that implements search runs."""
    a = make_search_handler("a", documents=[{"title": "A"}])
    b = make_search_handler("b", documents=[{"title": "B"}])
    c = make_search_handler("c", search_fields=())  # free-text only
    d = make_lookup_handler("d")
    handler_registry(a, b, c, d)

    results = search(SearchInput(input="query"))

    assert {r.source for r in results} == {"a", "b", "c"}
    assert all(r.status == "ok" for r in results)
    assert [r.documents for r in results] == [
        [{"title": "A"}],
        [{"title": "B"}],
        [{"title": "c"}],
    ]


def test_missing_capability(handler_registry: Any) -> None:
    """An explicitly requested source without search capability is reported as
    a no_match with an explanation (unknown names raise in ``resolve_handlers``,
    see ``test_dispatch.py``)."""
    handler_registry(make_lookup_handler("nosearch"))

    (result,) = search(SearchInput(input="q"), sources=["nosearch"])
    assert result.status == "no_match"
    assert "does not support search" in (result.message or "")


@pytest.mark.parametrize(
    ("query", "search_fields", "sources", "status", "message"),
    [
        # a source is not run when it cannot process every provided filter:
        # a partial query would silently answer a different question
        (
            SearchInput(input="quantum", filters={"author": ["E"], "title": ["T"]}),
            ("author",),
            None,
            "no_match",
            "cannot use filter(s): title",
        ),
        # without explicit sources, unusable candidates are still reported;
        # the client decides what to surface (pinned behaves the same)
        (
            SearchInput(input="", filters={"title": ["T"]}),
            ("author",),
            None,
            "no_match",
            "cannot use filter(s): title",
        ),
        # a handler that declares no fields works on free text only
        (
            SearchInput(input="", filters={"title": ["T"]}),
            (),
            ["a"],
            "no_match",
            "free-text only",
        ),
        (
            SearchInput(input="q", filters={"title": ["T"]}),
            (),
            ["a"],
            "no_match",
            "title",
        ),
        (SearchInput(input="q"), (), ["a"], "ok", None),
    ],
)
def test_field_usability(
    handler_registry: Any,
    query: SearchInput,
    search_fields: tuple[str, ...],
    sources: list[str] | None,
    status: str,
    message: str | None,
) -> None:
    handler_registry(make_search_handler("a", search_fields=search_fields))

    (result,) = search(query, sources=sources)
    assert result.status == status
    if message is None:
        assert result.message is None
    else:
        assert message in (result.message or "")


def test_failures_are_isolated(handler_registry: Any) -> None:
    """One handler's failure never suppresses another handler's result.

    The exception-to-message mapping itself belongs to ``dispatch.attempt``
    (see ``test_dispatch.py``); this pins that the flow reports it as
    ``failed``.
    """
    handler_registry(
        make_search_handler("bad", search_exc=SourceError("outage")),
        make_search_handler("good", documents=[{"title": "T"}]),
    )

    results = search(SearchInput(input="q"))
    assert [(r.source, r.status) for r in results] == [
        ("bad", "failed"),
        ("good", "ok"),
    ]
    assert results[0].message == "outage"


def test_max_results_passthrough(handler_registry: Any) -> None:
    """max_results reaches the handler (there are no per-handler options)."""
    seen: dict[str, Any] = {}

    handler_registry(
        make_search_handler(
            "a",
            documents=[{}],
            on_search=lambda query, max_results: seen.update(max_results=max_results),
        )
    )

    search(SearchInput(input="q"), sources=["a"], max_results=42)

    assert seen["max_results"] == 42


def test_none_output_is_a_failure(handler_registry: Any) -> None:
    """``search`` returns an output, so ``None`` is a broken contract, not an
    empty result: only ``parse`` declares an optional return."""
    handler_registry(make_search_handler("broken", returns_none=True))

    (result,) = search(SearchInput(input="q"), sources=["broken"])
    assert result.status == "failed"
    assert result.message is None


def test_no_result_is_not_an_error(handler_registry: Any) -> None:
    handler_registry(make_search_handler("a", documents=[]))

    results = search(SearchInput(input="q"), sources=["a"])
    assert results[0].status == "no_result"


def test_empty_query_raises(handler_registry: Any) -> None:
    """A query-less search is rejected at the boundary, before any handler
    runs."""
    handler_registry(make_search_handler("a"))

    with pytest.raises(ValueError, match="query or at least one filter"):
        search(SearchInput())

    # an empty filter list is not a constraint either
    with pytest.raises(ValueError, match="query or at least one filter"):
        search(SearchInput(filters={"title": []}))
