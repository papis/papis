from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.exceptions import SourceError
from papis.sources.handler import ParseInput
from papis.sources.parse import parse
from papis.testing import make_lookup_handler, make_parse_handler

if TYPE_CHECKING:
    from typing import Any


def test_fan_out_to_all_parseable(handler_registry: Any) -> None:
    """Without explicit sources, every handler that implements parse runs."""
    handler_registry(
        make_parse_handler("a", documents=[{"title": "A"}]),
        make_parse_handler("b", documents=[{"title": "B"}]),
        make_lookup_handler("c"),
    )

    results = parse(ParseInput(content="content"))

    assert [r.source for r in results] == ["a", "b"]
    assert all(r.status == "ok" for r in results)
    assert [r.documents for r in results] == [[{"title": "A"}], [{"title": "B"}]]


def test_missing_capability(handler_registry: Any) -> None:
    """An explicitly requested source without parse capability is reported as
    a no_match explaining the missing capability (unknown names raise in
    ``resolve_handlers``, see ``test_dispatch.py``)."""
    handler_registry(make_lookup_handler("noparse"))

    (result,) = parse(ParseInput(content="content"), sources=["noparse"])
    assert result.status == "no_match"
    assert result.message == "source does not support parse"


def test_decline_is_no_match(handler_registry: Any) -> None:
    """A parser that declines reports a bare no_match, pinned or not.

    The decline must stay distinguishable from a missing capability, which
    carries an explanatory message.
    """
    handler_registry(
        make_parse_handler("declining", returns_none=True),
        make_parse_handler("a", documents=[{"title": "A"}]),
    )

    (result,) = parse(ParseInput(content="content"), sources=["declining"])
    assert result.status == "no_match"
    assert result.message is None

    # unpinned, the decliner is reported like any other candidate
    results = parse(ParseInput(content="content"))
    assert [(r.source, r.status) for r in results] == [
        ("declining", "no_match"),
        ("a", "ok"),
    ]


def test_failures_are_isolated(handler_registry: Any) -> None:
    """One handler's failure never suppresses another handler's result.

    The exception-to-message mapping itself belongs to ``dispatch.attempt``
    (see ``test_dispatch.py``); this pins that the flow reports it as
    ``failed``.
    """
    handler_registry(
        make_parse_handler("broken", parse_exc=SourceError("down")),
        make_parse_handler("good", documents=[{"title": "A"}]),
    )

    results = parse(ParseInput(content="content"))
    assert [(r.source, r.status) for r in results] == [
        ("broken", "failed"),
        ("good", "ok"),
    ]
    assert results[0].message == "down"


def test_no_result_for_empty_documents(handler_registry: Any) -> None:
    """A recognized format with no documents is no_result (with its
    diagnostic message)."""
    handler_registry(make_parse_handler("empty", documents=[], message="nothing here"))

    results = parse(ParseInput(content="content"))
    assert len(results) == 1
    assert results[0].status == "no_result"
    assert results[0].message == "nothing here"


def test_message_propagation(handler_registry: Any) -> None:
    handler_registry(
        make_parse_handler("a", message="2 non-object element(s) ignored.")
    )

    results = parse(ParseInput(content="content"))
    assert len(results) == 1
    assert results[0].status == "ok"
    assert results[0].message == "2 non-object element(s) ignored."


def test_empty_content_raises(handler_registry: Any) -> None:
    """Content-less requests are rejected at the boundary, before any
    handler runs."""
    handler_registry(make_parse_handler("a"))

    with pytest.raises(ValueError, match="parse requires content"):
        parse(ParseInput())
