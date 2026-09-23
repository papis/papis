from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import papis.sources.handler as handler_module
from papis.sources.handler import (
    HandlerRegistry,
    LookupInput,
    LookupOutput,
    ParseOutput,
    SearchInput,
    SearchOutput,
    SourceHandler,
)
from papis.sources.handlers.dblp import DblpHandler
from papis.sources.handlers.doi import DoiHandler
from papis.sources.handlers.formats.yaml import YamlHandler
from papis.sources.handlers.isbn import IsbnHandler
from papis.sources.handlers.pmid import PmidHandler
from papis.sources.handlers.zenodo import ZenodoHandler
from papis.testing import make_lookup_handler
from tests.sources.helpers import make_registry

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any


def test_get(monkeypatch: pytest.MonkeyPatch) -> None:
    handler_cls = make_lookup_handler("fake")
    registry = make_registry(monkeypatch, handler_cls)

    assert registry.get("fake") is handler_cls
    assert registry.get("nope") is None


def test_load_keys_by_name_and_skips_invalid_plugins(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Discovery keys by the handler's ``name``, skips invalid entry points
    with a warning, and runs exactly once."""
    import papis.plugin

    handler_cls = make_lookup_handler("fake")
    calls: list[str] = []

    def get_plugins(namespace: str) -> dict[str, Any]:
        calls.append(namespace)
        if namespace == "papis.source":
            return {"good": handler_cls, "bad": object()}
        return {}

    monkeypatch.setattr(papis.plugin, "get_plugins", get_plugins)

    registry = HandlerRegistry()
    with caplog.at_level("WARNING", logger="papis.sources.handler"):
        registry.load()

    # keyed by the handler's name, not the entry point's
    assert registry.get("fake") is handler_cls
    assert registry.get("good") is None
    assert any(
        "not a SourceHandler subclass" in record.message for record in caplog.records
    )

    registry.load()
    assert calls.count("papis.source") == 1


def test_discover_plugin_name_clashes(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Two plugins claiming one name: the first claim wins, the other is
    warned about and dropped, never silently shadowed or shadowing."""
    import papis.plugin
    import papis.sources.legacy as legacy_module

    first = make_lookup_handler("shared")
    second = make_lookup_handler("shared")

    monkeypatch.setattr(
        papis.plugin,
        "get_plugins",
        lambda namespace: (
            {"first": first, "second": second} if namespace == "papis.source" else {}
        ),
    )
    monkeypatch.setattr(legacy_module, "wrap_legacy_plugins", lambda: {})

    with caplog.at_level("WARNING", logger="papis.sources.handler"):
        handlers = handler_module.discover_handlers()

    assert handlers == {"shared": first}
    assert sum("already claimed" in record.message for record in caplog.records) == 1


def test_discover_prefers_native_over_legacy(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Native handlers shadow same-named legacy wrappers, so a migrated
    source never double-runs; the deprecation warning lists only the
    wrappers that survive."""
    import papis.plugin
    import papis.sources.legacy as legacy_module

    native = make_lookup_handler("migrated")
    shadowed = make_lookup_handler("migrated", is_legacy=True)
    wrapped = make_lookup_handler("old", is_legacy=True)

    monkeypatch.setattr(
        papis.plugin,
        "get_plugins",
        lambda namespace: {"migrated": native} if namespace == "papis.source" else {},
    )
    monkeypatch.setattr(
        legacy_module,
        "wrap_legacy_plugins",
        lambda: {"migrated": shadowed, "old": wrapped},
    )

    with caplog.at_level("WARNING", logger="papis.sources.handler"):
        handlers = handler_module.discover_handlers()

    assert handlers == {"migrated": native, "old": wrapped}

    [deprecation] = [r for r in caplog.records if r.name == "papis.sources.handler"]
    assert deprecation.levelname == "WARNING"
    assert "deprecated and will be removed in Papis 0.18" in deprecation.message
    assert "'old'" in deprecation.message and "'migrated'" not in deprecation.message


def test_capabilities_are_derived() -> None:
    """Capabilities are the optional methods a handler overrides — derived
    when the class is created, never declared — so a handler cannot claim a
    capability it lacks or have one the flows never see."""

    class Plain(SourceHandler):
        name = "plain"

        @classmethod
        def match_for_lookup(cls, evidence: LookupInput) -> SourceHandler | None:
            return None

        # ruff: ignore[no-self-use]
        def lookup(self, evidence: LookupInput) -> LookupOutput:
            return LookupOutput()

    class Searcher(Plain):
        @classmethod
        def search(cls, query: SearchInput, *, max_results: int) -> SearchOutput:
            return SearchOutput()

    class Parser(Plain):
        @classmethod
        def parse(cls, content: str) -> ParseOutput | None:
            return ParseOutput()

    class Both(Searcher, Parser):
        pass

    assert Plain.capabilities == frozenset({"lookup"})
    assert Searcher.capabilities == frozenset({"lookup", "search"})
    assert Parser.capabilities == frozenset({"lookup", "parse"})
    # inherited overrides count: a family implementing `parse` once at the
    # top is parsable all the way down
    assert Both.capabilities == frozenset({"lookup", "search", "parse"})


def test_registry_contains_all_entry_points() -> None:
    """Every ``papis.source`` entry point must be registered."""
    import importlib.metadata as md

    entry_points = set(md.entry_points(group="papis.source").names)
    registered = {cls.name for cls in handler_module.registry}
    missing = sorted(entry_points - registered)
    assert not missing, f"missing handlers: {missing}"


def test_match_is_deterministic_across_handlers() -> None:
    """Re-matching the same evidence must give the same match state:
    :meth:`match_for_lookup` is a pure classifier, not a step whose result may
    drift."""
    from papis.sources.client import CLIENT_HANDLERS

    samples = (
        LookupInput(input="1701.08223"),
        LookupInput(input="10.1103/physrevb.89.140501"),
        LookupInput(
            input="https://example.com/article", kind="webpage", content="<html></html>"
        ),
        LookupInput(input="", fields={"title": "A title"}),
    )

    def assert_same_state(handler_cls: type[SourceHandler]) -> None:
        for evidence in samples:
            first = handler_cls.match_for_lookup(evidence)
            second = handler_cls.match_for_lookup(evidence)

            assert (first is None) == (second is None)
            if first is not None:
                assert vars(first) == vars(second)

    for handler_cls in handler_module.registry:
        # NOTE: legacy adapters may have impure matches (their documented
        # bridge behavior); the determinism contract applies to native handlers
        if getattr(handler_cls, "is_legacy", False):
            continue

        assert_same_state(handler_cls)

    # NOTE: client source handlers match the submitted item and may do IO,
    # but the same determinism contract applies to them
    for handler_cls in CLIENT_HANDLERS:
        assert_same_state(handler_cls)


@pytest.mark.parametrize(
    ("handler_cls", "input_str"),
    [
        (DblpHandler, "conf/iccg/EncarnacaoAFFGM93"),
        (DoiHandler, "10.1103/paper.pdf"),
        (IsbnHandler, "9780486670478"),
        (PmidHandler, "28012456"),
        (ZenodoHandler, "7391177"),
        (YamlHandler, "title: My Paper.yaml"),
    ],
)
def test_match_ignores_the_filesystem(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    handler_cls: type[SourceHandler],
    input_str: str,
) -> None:
    """``match_for_lookup`` does no IO: an existing path shaped like an
    identifier is claimed like any other input."""
    monkeypatch.chdir(tmp_path)
    path = tmp_path / input_str
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()

    assert handler_cls.match_for_lookup(LookupInput(input=input_str)) is not None
