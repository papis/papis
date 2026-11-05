"""Shared fakes and helpers for the source-system tests (not a test module)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import papis.sources.handler as handler_module
from papis.sources.handler import (
    HandlerRegistry,
    LookupInput,
    LookupOutput,
    SourceHandler,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from typing import Any

    from papis.testing import ResourceCache


def make_registry(
    monkeypatch: pytest.MonkeyPatch,
    *classes: type[SourceHandler],
) -> HandlerRegistry:
    """A registry holding exactly *classes*, with nothing else to discover.

    Unlike the :func:`handler_registry` fixture, this builds a standalone
    ``HandlerRegistry`` and leaves the process-wide one alone: use it to test
    registry mechanics, not to run the flows.
    """
    monkeypatch.setattr(
        handler_module, "discover_handlers", lambda: {cls.name: cls for cls in classes}
    )
    return HandlerRegistry()


class FakeSession:
    """The part of a ``requests.Session`` the HTTP handlers use."""

    def __init__(self, content: str | bytes = "", status_code: int = 200) -> None:
        self.content = content.encode() if isinstance(content, str) else content
        self.status_code = status_code
        self.ok = 200 <= status_code < 400

    def get(
        self,
        url: str,
        params: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> FakeSession:
        return self

    def __enter__(self) -> FakeSession:
        return self

    def __exit__(self, *args: Any) -> None:
        return None


def lookup_page(
    handler_cls: type[SourceHandler],
    resource_cache: ResourceCache,
    name: str,
    url: str,
    *,
    adjust_expected: Callable[[dict[str, Any]], None] | None = None,
) -> LookupOutput:
    """Match *url* against the saved page ``<name>.html`` and look it up,
    checking the document against ``<name>_Out.json``.

    *adjust_expected* can modify the expected document in place, e.g. to
    account for parser-version differences.
    """
    content = resource_cache.get_remote_resource(f"{name}.html", url).decode()
    evidence = LookupInput(input=url, kind="webpage", content=content)

    handler = handler_cls.match_for_lookup(evidence)
    assert handler is not None

    result = handler.lookup(evidence)
    assert result.document is not None
    expected = resource_cache.get_local_resource(f"{name}_Out.json", result.document)
    if adjust_expected is not None:
        adjust_expected(expected)
    assert result.document == expected
    return result


def assert_match_cases(
    handler_cls: type[SourceHandler],
    *,
    matched: Iterable[str],
    rejected: Iterable[str],
) -> None:
    """Assert a site handler's URL matching."""
    for url in matched:
        # NOTE: matching is a pure URL/ID check, so it holds with or without the
        # gathered page
        assert handler_cls.match_for_lookup(LookupInput(input=url)) is not None, url
        assert (
            handler_cls.match_for_lookup(
                LookupInput(input=url, kind="webpage", content="<html></html>")
            )
            is not None
        ), url

    for url in rejected:
        assert handler_cls.match_for_lookup(LookupInput(input=url)) is None, url


def assert_bibtex_followup(result: LookupOutput, url: str) -> None:
    """Assert that the result asks for the BibTeX export at *url*."""
    assert result.followup is not None
    assert (result.followup.url, result.followup.format) == (url, "bibtex")


def assert_no_contribution(result: LookupOutput) -> None:
    """Assert that the handler contributed nothing to the lookup."""
    assert result.document is None
    assert result.files == []
    assert result.followup is None


def disable_doi_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make consulting the DOI source a test failure."""
    import papis.crossref

    def fail(doi: str) -> None:
        pytest.fail(f"the DOI source must not be consulted for '{doi}'")

    monkeypatch.setattr(papis.crossref, "doi_to_data", fail)
