"""Tests for the client source handlers (``papis.sources.client``)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest

import papis.config
import papis.document
import papis.tui.utils
import papis.utils
from papis.gather import gather
from papis.sources.client import (
    FolderClientHandler,
    LibraryClientHandler,
    get_known_sources,
    log_source_result,
    lookup_item,
    merge,
    search_item,
)
from papis.sources.handler import FileReference, LookupInput, SearchInput
from papis.sources.lookup import LookupResult, run_handler
from papis.testing import make_lookup_handler, make_search_handler

if TYPE_CHECKING:
    from typing import Any

    from papis.sources.dispatch import Status
    from papis.testing import TemporaryLibrary


def _make_folder(tmp_library: Any, name: str = "test-client-folder") -> tuple[str, str]:
    """Create a Papis document folder; returns ``(folder, file_path)``."""
    import os

    from papis.testing import create_random_file
    from papis.yaml import data_to_yaml

    folder = os.path.join(tmp_library.tmpdir, name)
    os.makedirs(folder)
    file_path = create_random_file(dir=folder)
    data_to_yaml(
        os.path.join(folder, "info.yaml"),
        {
            "author": "Plato",
            "title": "Republic",
            "files": [os.path.basename(file_path)],
        },
    )
    return folder, file_path


def test_folder_lookup(tmp_library: TemporaryLibrary) -> None:
    folder, file_path = _make_folder(tmp_library)

    record = run_handler(FolderClientHandler, LookupInput(input=folder))
    assert record.source == "folder"
    assert record.status == "ok"
    assert record.document is not None
    assert record.document["title"] == "Republic"
    assert record.document["author"] == "Plato"
    # NOTE: 'files' in the document data is dropped (see
    # 'FolderClientHandler.lookup')
    assert "files" not in record.document
    # NOTE: client files ride the record's file references as local paths, so
    # the caller's '--download-files' gate applies to them like source files
    assert record.files == [FileReference(path=file_path)]


def test_library_lookup(
    tmp_library: TemporaryLibrary, monkeypatch: pytest.MonkeyPatch
) -> None:
    import papis.pick

    # NOTE: pick the document with the most files for a deterministic test
    monkeypatch.setattr(
        papis.pick,
        "pick",
        lambda x, **k: [max(x, key=lambda d: len(d.get_files()))] if x else [],
    )

    record = run_handler(LibraryClientHandler, LookupInput(input=tmp_library.libname))
    assert record.source == "lib"
    assert record.status == "ok"
    assert record.document is not None
    # the library delegates to the folder source: metadata without 'files'
    assert "title" in record.document
    assert "files" not in record.document
    assert record.files

    # a cancelled picker is not an error, but it produced no result
    monkeypatch.setattr(papis.pick, "pick", lambda x, **k: [])
    record = run_handler(LibraryClientHandler, LookupInput(input=tmp_library.libname))
    assert record.status == "no_result"
    assert record.document is None
    assert record.files == []


def test_unknown_item_declines(tmp_library: TemporaryLibrary) -> None:
    """``match_for_lookup`` classifies the input first: an unknown folder or library
    declines instead of failing."""
    import os

    missing = os.path.join(tmp_library.tmpdir, "nope")

    assert (
        run_handler(FolderClientHandler, LookupInput(input=missing)).status
        == "no_match"
    )
    assert (
        run_handler(LibraryClientHandler, LookupInput(input="nope")).status
        == "no_match"
    )


def test_lookup_item_pinned_sources(
    handler_registry: Any, client_registry: Any
) -> None:
    handler_registry(
        make_lookup_handler(
            "fake-handler", document={"title": "remote", "author": "remote-author"}
        )
    )
    client_registry(make_lookup_handler("fake-client", document={"title": "client"}))

    # unpinned: both passes run (a string can be a library name and an
    # identifier); client results win equal-priority ties
    results = lookup_item(gather("some-item").evidence)
    assert [result.source for result in results] == ["fake-handler", "fake-client"]
    data, _ = merge(results)
    assert data["title"] == "client"
    assert data["author"] == "remote-author"

    # pinned: only the named source runs ('--from' pins one source per name)
    results = lookup_item(gather("x").evidence, ("fake-client",))
    assert [result.source for result in results] == ["fake-client"]
    results = lookup_item(gather("x").evidence, ("fake-handler",))
    assert [result.source for result in results] == ["fake-handler"]

    # a declining client is hidden when unpinned
    client_registry(make_lookup_handler("fake-client", match_result=False))
    results = lookup_item(gather("x").evidence)
    assert [result.source for result in results] == ["fake-handler"]

    with pytest.raises(ValueError, match="unknown source 'nope'"):
        lookup_item(gather("x").evidence, ("nope",))


def test_lookup_item_pinned_client_declines(
    handler_registry: Any, client_registry: Any
) -> None:
    """``match_for_lookup`` classifies pinned client inputs too: a decline is a
    ``no_match`` record (the CLI warns), not a usage error."""
    handler_registry()
    client_registry(make_lookup_handler("fake-client", match_result=False))

    (result,) = lookup_item(gather("x").evidence, ("fake-client",))
    assert result.source == "fake-client"
    assert result.status == "no_match"
    assert result.document is None


def test_lookup_item_unpinned_failures_surface(
    handler_registry: Any, client_registry: Any
) -> None:
    """Unlike declines, a failing client source surfaces even when unpinned."""
    handler_registry()
    client_registry(make_lookup_handler("broken", lookup_exc=RuntimeError("boom")))

    results = lookup_item(gather("x").evidence)
    (result,) = results
    assert result.source == "broken"
    assert result.status == "failed"


def test_lookup_item_empty_evidence_is_a_usage_error(
    handler_registry: Any, client_registry: Any
) -> None:
    handler_registry(make_lookup_handler("fake-handler"))
    client_registry()

    with pytest.raises(ValueError, match="input string"):
        lookup_item(gather("").evidence, ("fake-handler",))


def test_get_known_sources(handler_registry: Any, client_registry: Any) -> None:
    """Every known source handler (server and client) is listed, sorted; a
    capability narrows the list."""
    from papis.sources.handlers.doi import DoiHandler
    from papis.sources.handlers.isbn import IsbnHandler

    handler_registry(DoiHandler, IsbnHandler)
    client_registry(make_lookup_handler("client-a"), LibraryClientHandler)

    assert [cls.name for cls in get_known_sources()] == [
        "client-a",
        "doi",
        "isbn",
        "lib",
    ]
    assert [cls.name for cls in get_known_sources(capability="search")] == [
        "isbn",
        "lib",
    ]


def test_library_search(
    tmp_library: TemporaryLibrary, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without a 'library' filter the configured default library is searched."""
    (result,) = search_item(SearchInput(input="krishnamurti"), ["lib"])
    assert result.source == "lib"
    assert result.status == "ok"
    assert any(d.get("author") == "J. Krishnamurti" for d in result.documents)

    # a 'library' filter selects the library *instead of* the default one
    monkeypatch.setattr(papis.config, "get_lib_name", lambda: "not-a-library")

    (result,) = search_item(
        SearchInput(input="krishnamurti", filters={"library": [tmp_library.libname]}),
        ["lib"],
    )
    assert result.status == "ok"
    assert any(d.get("author") == "J. Krishnamurti" for d in result.documents)


def test_library_search_without_query_runs_configured_query(
    tmp_library: TemporaryLibrary,
) -> None:
    """'default-query-string' is a real query, not only a match-all sentinel."""
    papis.config.set("default-query-string", "author:Krishnamurti")

    (result,) = search_item(
        SearchInput(filters={"library": [tmp_library.libname]}), ["lib"]
    )
    assert result.status == "ok"
    assert [d["title"] for d in result.documents] == ["Freedom from the known"]


def _record_filters(seen: dict[str, Any], key: str) -> Any:
    """An ``on_search`` hook that records the filters a source was queried with."""
    return lambda query, max_results: seen.update({key: dict(query.filters)})


def _search_sources(seen: dict[str, Any]) -> tuple[Any, ...]:
    """The remote/local pair used by the search_item tests, both recording
    the filters they receive into *seen*."""
    return (
        make_search_handler(
            "remote",
            documents=[{"title": "R"}],
            on_search=_record_filters(seen, "remote_filters"),
        ),
        make_search_handler(
            "fake-client",
            documents=[{"title": "C"}],
            on_search=_record_filters(seen, "filters"),
        ),
    )


def test_search_item_order(handler_registry: Any, client_registry: Any) -> None:
    """Results follow the requested order, whether a source ran locally or
    remotely."""
    seen: dict[str, Any] = {}
    remote, client = _search_sources(seen)
    handler_registry(remote)
    client_registry(client)

    results = search_item(
        SearchInput(input="q", filters={"author": ["A"], "title": ["T"]}),
        ["fake-client", "remote"],
    )
    assert [r.source for r in results] == ["fake-client", "remote"]
    assert seen["filters"] == {"author": ["A"], "title": ["T"]}
    assert seen["remote_filters"] == {"author": ["A"], "title": ["T"]}


def test_search_item_boundaries(handler_registry: Any, client_registry: Any) -> None:
    """Filter gating and empty-query errors."""
    remote, client = _search_sources({})
    handler_registry(remote)
    client_registry(client)

    # the filter gate applies to client sources as well
    (result,) = search_item(
        SearchInput(input="q", filters={"journal": ["J"]}), ["fake-client"]
    )
    assert result.status == "no_match"
    assert "cannot use filter(s): journal" in (result.message or "")

    # empty filter values are not constraints: the request is rejected at the
    # boundary instead of searching everything
    with pytest.raises(ValueError, match="query or at least one filter"):
        search_item(SearchInput(filters={"title": []}), ["remote"])

    with pytest.raises(ValueError, match="unknown source 'nope'"):
        search_item(SearchInput(input="q"), ["nope"])

    with pytest.raises(ValueError, match="query or at least one filter"):
        search_item(SearchInput(), ["fake-client"])


def _result(
    source: str,
    document: dict[str, Any] | None = None,
    *,
    priority: int = 5,
    files: list[FileReference] | None = None,
    status: Status = "ok",
) -> LookupResult:
    """Construct a source result for testing."""
    return LookupResult(
        source=source,
        priority=priority,
        status=status,
        document=document,
        files=files or [],
    )


def test_merge_fold_order() -> None:
    first = _result("crossref", {"title": "First", "a": 1})
    second = _result("aps", {"title": "Second", "b": 2})

    # the results list is the precedence order: later entries overwrite
    # earlier ones and priorities are not consulted
    data, _ = merge([first, second])
    assert data == {"title": "Second", "a": 1, "b": 2}
    data, _ = merge([second, first])
    assert data == {"title": "First", "a": 1, "b": 2}


def test_merge_base() -> None:
    base = {"title": "From base", "year": 2020}
    result = _result("crossref", {"title": "From source"})

    data, _ = merge([result], base=base)
    assert data == {"title": "From source", "year": 2020}
    # the caller's base is not mutated
    assert base == {"title": "From base", "year": 2020}


def test_merge_ref_key_is_dropped() -> None:
    result = _result("bibtex", {"ref": "some_ref", "title": "T"})

    data, _ = merge([result])
    assert data == {"title": "T"}

    # a document that is only a 'ref' contributes nothing
    data, _ = merge([_result("bibtex", {"ref": "some_ref"})])
    assert data == {}


def test_merge_files() -> None:
    # files accumulate in fold order, also from results without a document
    # (handlers whose document arrives via a followup)
    first = _result(
        "zenodo",
        {"title": "Z"},
        files=[FileReference(url="https://zenodo.org/files/1")],
    )
    second = _result("crossref", files=[FileReference(path="/tmp/paper.pdf")])

    data, files = merge([first, second])
    assert data == {"title": "Z"}
    assert [(ref.url, ref.path) for ref in files] == [
        ("https://zenodo.org/files/1", None),
        (None, "/tmp/paper.pdf"),
    ]


def test_merge_pick_follows_selection_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The selection order is the fold order: the last source wins and the
    first chunk of data merges without prompting."""
    monkeypatch.setattr(
        papis.tui.utils, "select_range", lambda options, message, **kwargs: [1, 0]
    )

    def _accept(document: dict[str, Any], data: dict[str, Any], name: str) -> None:
        document.update(data)

    monkeypatch.setattr(papis.utils, "update_doc_from_data_interactively", _accept)

    data, files = merge(
        [
            _result("src-a", {"title": "A"}),
            _result(
                "src-b",
                {"title": "B", "only-b": "1"},
                files=[FileReference(path="b.pdf")],
            ),
        ],
        pick=True,
        resolve_fields=True,
    )

    assert data == {"title": "A", "only-b": "1"}
    assert [ref.path for ref in files] == ["b.pdf"]


def test_merge_pick_lists_description_and_file_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The selection list shows the source, the document's description and how
    many files come with it: file identities matter less than that they exist."""
    options: list[str] = []

    def _select(candidates: list[str], message: str, **kwargs: Any) -> list[int]:
        options.extend(candidates)
        return [0, 1, 2, 3]

    monkeypatch.setattr(papis.tui.utils, "select_range", _select)
    monkeypatch.setattr(
        papis.utils, "update_doc_from_data_interactively", lambda *args: None
    )

    # NOTE: the description is subject to 'document-description-format', so stub
    # it to keep this test independent of the user's configuration
    monkeypatch.setattr(
        papis.document,
        "describe",
        lambda document: "; ".join(f"{k}={v}" for k, v in document.items()),
    )

    merge(
        [
            _result("doi", {"title": "A", "author": "Smith"}),
            _result(
                "fallback",
                {"title": "Redirecting"},
                files=[FileReference(url="https://example.org/paper.pdf")],
            ),
            _result(
                "zenodo",
                {"title": "B", "author": "Doe"},
                files=[
                    FileReference(url="https://zenodo.org/1.pdf"),
                    FileReference(url="https://zenodo.org/2.pdf"),
                ],
            ),
            # a source may return a document without a title to show
            _result(
                "no-title",
                {"author": "X"},
                files=[FileReference(path="/tmp/a.pdf")],
            ),
        ],
        pick=True,
        resolve_fields=True,
    )

    assert options == [
        "[doi] title=A; author=Smith (files: none)",
        "[fallback] title=Redirecting (files: 1)",
        "[zenodo] title=B; author=Doe (files: 2)",
        "[no-title] author=X (files: 1)",
    ]


def test_merge_resolve_fields_offers_incoming_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without 'pick' there is no source selection: explicit results ('--from')
    fold in list order. With a base nothing merges silently and every incoming
    key is offered (legacy behavior)."""
    calls: list[tuple[dict[str, Any], str]] = []

    def _record(document: dict[str, Any], data: dict[str, Any], name: str) -> None:
        calls.append((dict(data), name))

    def _fail(options: Any, message: str, **kwargs: Any) -> list[int]:
        raise AssertionError("explicit results must not be offered for selection")

    monkeypatch.setattr(papis.utils, "update_doc_from_data_interactively", _record)
    monkeypatch.setattr(papis.tui.utils, "select_range", _fail)

    data, _ = merge(
        [_result("src-a", {"title": "A"}), _result("src-b", {"title": "B"})],
        base={"title": "Base"},
        resolve_fields=True,
    )

    assert calls == [({"title": "A"}, "src-a"), ({"title": "B"}, "src-b")]
    assert data == {"title": "Base"}


def test_merge_pick_single_candidate_is_silent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A single document-bearing result needs no selection."""

    def _fail(options: Any, message: str, **kwargs: Any) -> list[int]:
        raise AssertionError("a single candidate must not be offered for selection")

    monkeypatch.setattr(papis.tui.utils, "select_range", _fail)

    data, files = merge(
        [
            _result("src-a", {"title": "A"}),
            _result("src-b", files=[FileReference(path="b.pdf")]),
        ],
        pick=True,
    )

    assert data == {"title": "A"}
    assert [ref.path for ref in files] == ["b.pdf"]


def test_merge_pick_drops_deselected_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A deselected result contributes neither data nor files."""
    monkeypatch.setattr(
        papis.tui.utils, "select_range", lambda options, message, **kwargs: [0]
    )

    def _accept(document: dict[str, Any], data: dict[str, Any], name: str) -> None:
        document.update(data)

    monkeypatch.setattr(papis.utils, "update_doc_from_data_interactively", _accept)

    data, files = merge(
        [
            _result("src-a", {"title": "A"}),
            _result("src-b", {"title": "B"}, files=[FileReference(path="b.pdf")]),
        ],
        pick=True,
        resolve_fields=True,
    )

    assert data == {"title": "A"}
    assert files == []


def test_log_source_result_failures_warn(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger(__name__)

    with caplog.at_level(logging.WARNING, logger=logger.name):
        log_source_result(
            logger,
            LookupResult(source="fake", priority=5, status="failed", message="boom"),
        )

    assert "Source 'fake' failed: boom" in caplog.text


def test_log_source_result_no_match_only_for_requested_sources(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A fan-out decline is silent; a pinned source gets the default text."""
    logger = logging.getLogger(__name__)
    result = LookupResult(source="fake", priority=5, status="no_match")

    with caplog.at_level(logging.WARNING, logger=logger.name):
        log_source_result(logger, result)
        log_source_result(logger, result, sources={"fake"})

    records = [record for record in caplog.records if record.name == logger.name]
    assert len(records) == 1
    assert "Source 'fake': did not match the given input" in caplog.text


def test_log_source_result_ok_caveat_is_surfaced(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger(__name__)

    with caplog.at_level(logging.INFO, logger=logger.name):
        log_source_result(
            logger,
            LookupResult(source="fake", priority=5, status="ok", message="2 entries"),
        )

    assert "Source 'fake' returned a result." in caplog.text
    assert "2 entries" in caplog.text
