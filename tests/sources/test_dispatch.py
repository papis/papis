"""Tests for the shared dispatch machinery (``papis.sources.dispatch``)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.exceptions import SourceError
from papis.sources.dispatch import attempt, resolve_handlers
from papis.testing import make_lookup_handler, make_parse_handler, make_search_handler

if TYPE_CHECKING:
    from typing import Any

    import pytest as pytest_type


def test_resolve_all_by_capability(handler_registry: Any) -> None:
    """Without explicit sources, only handlers with the needed capability run.

    ``lookup`` is required of every handler, so a ``lookup`` request reaches
    them all.
    """
    handler_registry(
        make_lookup_handler("plain"),
        make_search_handler("searcher"),
        make_parse_handler("parser"),
    )

    assert [cls.name for cls in resolve_handlers(None, capability="search")] == [
        "searcher"
    ]
    assert [cls.name for cls in resolve_handlers(None, capability="parse")] == [
        "parser"
    ]
    assert [cls.name for cls in resolve_handlers(None, capability="lookup")] == [
        "plain",
        "searcher",
        "parser",
    ]


def test_resolve_requested_names(handler_registry: Any) -> None:
    """Explicit names are returned as given: no capability filter (the flow
    reports the missing capability) and no reordering."""
    handler_registry(make_lookup_handler("plain"), make_search_handler("searcher"))

    handlers = resolve_handlers(["searcher", "plain"], capability="search")
    assert [cls.name for cls in handlers] == ["searcher", "plain"]


def test_resolve_unknown_name(handler_registry: Any) -> None:
    handler_registry(make_lookup_handler("known"))

    with pytest.raises(ValueError, match="unknown source 'bogus'"):
        resolve_handlers(["bogus"], capability="lookup")


def test_attempt_value() -> None:
    """A successful call passes its value through, with no message."""

    def lookup() -> str:
        return "value"

    assert attempt("fake", lookup) == ("value", None)


def test_attempt_expected_failure(
    caplog: pytest_type.LogCaptureFixture,
) -> None:
    """``SourceError`` is the handler saying "no": the message is the error
    text and it is logged at DEBUG, so a dead site does not print a traceback.
    """

    def lookup() -> None:
        raise SourceError("outage")

    with caplog.at_level("DEBUG", logger="papis.sources.dispatch"):
        assert attempt("fake", lookup) == (None, "outage")

    (record,) = caplog.records
    assert record.levelname == "DEBUG"
    # the action is the handler method's name
    assert "failed to lookup" in record.message
    assert record.exc_info is not None


def test_attempt_unexpected_failure(
    caplog: pytest_type.LogCaptureFixture,
) -> None:
    """Anything else is a bug: the message keeps the exception type *and* its
    text (so a ``KeyError`` names the missing key), and the record is an ERROR
    carrying the traceback."""

    def search() -> None:
        raise RuntimeError("bug")

    with caplog.at_level("DEBUG", logger="papis.sources.dispatch"):
        assert attempt("fake", search) == (None, "RuntimeError: bug")

    (record,) = caplog.records
    assert record.levelname == "ERROR"
    assert "failed to search unexpectedly" in record.message
    assert record.exc_info is not None
