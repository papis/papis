from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any, cast

from papis.testing import PapisRunner, TemporaryLibrary, make_search_handler

if TYPE_CHECKING:
    import pytest


def _explore_export(tmp_library: TemporaryLibrary,
                    chain: list[str],
                    outname: str) -> list[dict[str, object]]:
    # NOTE: Tests use this function not to check if JSON export is correct, but rather
    # to check whether the explorer's internal data processing is correct.
    from papis.commands.explore import cli

    outfile = os.path.join(tmp_library.tmpdir, outname)
    result = PapisRunner().invoke(
        cli, [*chain, "export", "--format", "json", "--out", outfile])
    assert result.exit_code == 0

    with open(outfile, encoding="utf-8") as fd:
        return cast("list[dict[str, object]]", json.load(fd))


def _install_search_registry(install: Any, *names: str) -> None:
    """Install searchable sources that echo the query they were given."""
    def echo_query(name: str) -> Any:
        def documents(query: Any, max_results: int) -> list[dict[str, Any]]:
            return [{
                "title": f"{name}: {query.input}",
                "filters": dict(query.filters),
                "max_results": max_results,
            }]
        return documents

    install(*(make_search_handler(n, documents=echo_query(n)) for n in names))


def test_explore_source_search(tmp_library: TemporaryLibrary,
                               handler_registry: Any,
                               caplog: pytest.LogCaptureFixture) -> None:
    """Sources are subcommands; the query is an option and filters combine with AND."""
    _install_search_registry(handler_registry, "crossref", "arxiv")
    from papis.commands.explore import cli

    with caplog.at_level("INFO"):
        result = PapisRunner().invoke(
            cli, ["crossref",
                  "-f", "author:A", "--filter", "author:B",
                  "--filter", "title:T", "-m", "5",
                  "-q", "einstein",
                  "arxiv", "--query", "witten",
                  "export", "--format", "json"])
    assert result.exit_code == 0
    assert "Searching 'crossref' for documents." in caplog.text
    assert "Searching 'arxiv' for documents." in caplog.text

    data = json.loads(result.output)
    assert [d["title"] for d in data] == [
        "crossref: einstein", "arxiv: witten"]
    assert data[0]["filters"] == {"author": ["A", "B"], "title": ["T"]}
    assert data[0]["max_results"] == 5


def test_explore_malformed_filter(
        tmp_library: TemporaryLibrary,
        caplog: pytest.LogCaptureFixture) -> None:
    """A filter without a value is an error, but not a crash."""
    from papis.commands.explore import cli

    with caplog.at_level("ERROR"):
        result = PapisRunner().invoke(
            cli, ["crossref", "--filter", "author"])

    assert result.exit_code == 1
    assert "Malformed filter 'author'" in caplog.text


def test_explore_search_no_match_warns(
        tmp_library: TemporaryLibrary,
        handler_registry: Any,
        caplog: pytest.LogCaptureFixture) -> None:
    """A pinned source that cannot use the filter is warned about, with the
    service's explanation."""
    _install_search_registry(handler_registry, "crossref")
    from papis.commands.explore import cli

    with caplog.at_level("WARNING"):
        result = PapisRunner().invoke(
            cli, ["crossref", "--filter", "journal:Nature"])

    assert result.exit_code == 0
    assert "Source 'crossref': cannot use filter(s): journal" in caplog.text


def test_explore_search_missing_query_is_an_error(
        tmp_library: TemporaryLibrary,
        handler_registry: Any,
        caplog: pytest.LogCaptureFixture) -> None:
    """A search with no query and no filters is rejected at the request
    boundary as an error."""
    _install_search_registry(handler_registry, "crossref")
    from papis.commands.explore import cli

    with caplog.at_level("ERROR"):
        result = PapisRunner().invoke(cli, ["crossref"])

    assert result.exit_code == 1
    assert "search requires a query" in caplog.text


def test_explore_search_does_not_consume_next_subcommand(
        tmp_library: TemporaryLibrary,
        handler_registry: Any,
        caplog: pytest.LogCaptureFixture) -> None:
    """The query is an option, so a following subcommand name is not mistaken
    for it (an optional positional would swallow ``pick``)."""
    _install_search_registry(handler_registry, "crossref")
    from papis.commands.explore import cli

    with caplog.at_level("ERROR"):
        result = PapisRunner().invoke(cli, ["crossref", "pick"])

    assert result.exit_code == 1
    assert "search requires a query" in caplog.text


def test_explore_lib(tmp_library: TemporaryLibrary) -> None:
    data = _explore_export(
        tmp_library, ["lib", "-q", "krishnamurti"], "lib_out.json")

    assert len(data) == 1
    assert data[0]["title"] == "Freedom from the known"


def test_explore_parse(tmp_library: TemporaryLibrary) -> None:
    bibfile = os.path.join(tmp_library.tmpdir, "test.bib")
    with open(bibfile, "w", encoding="utf-8") as fd:
        fd.write(
            "@article{test,\n"
            "  author = {D. Bohm},\n"
            "  title = {Quantum Theory}\n"
            "}\n")

    data = _explore_export(tmp_library, ["bibtex", bibfile], "parse_out.json")

    assert len(data) == 1
    assert data[0]["title"] == "Quantum Theory"


def test_explore_parse_without_content(
        tmp_library: TemporaryLibrary,
        caplog: pytest.LogCaptureFixture) -> None:
    """A binary file (no text content) is warned about, not a traceback."""
    from papis.commands.explore import cli

    binaryfile = os.path.join(tmp_library.tmpdir, "test.bin")
    with open(binaryfile, "wb") as fd:
        fd.write(b"\xff\xfe\x00\x00")

    with caplog.at_level("WARNING"):
        result = PapisRunner().invoke(cli, ["bibtex", binaryfile])

    assert result.exit_code == 0
    assert "Could not parse" in caplog.text


def test_explore_parse_surfaces_diagnostics(
        tmp_library: TemporaryLibrary,
        caplog: pytest.LogCaptureFixture) -> None:
    """The chosen format reports its own caveats; no other format is probed."""
    jsonfile = os.path.join(tmp_library.tmpdir, "test.json")
    with open(jsonfile, "w", encoding="utf-8") as fd:
        json.dump([{"title": "First"}, 42], fd)

    with caplog.at_level("WARNING"):
        data = _explore_export(tmp_library, ["json", jsonfile], "diag_out.json")

    assert len(data) == 1
    assert data[0]["title"] == "First"
    # the dropped non-object element is reported by the json handler
    assert "non-object" in caplog.text
    # the other formats are not tried, so they cannot report anything
    assert "non-dict" not in caplog.text
    assert "did not match" not in caplog.text


def _make_library_document(tmp_library: TemporaryLibrary,
                           name: str,
                           data: dict[str, Any],
                           nfiles: int = 0) -> None:
    """Create a document in the temporary library, with *nfiles* attachments."""
    from papis.document import Document
    from papis.id import ID_KEY_NAME, compute_an_id
    from papis.testing import create_random_file

    folder = os.path.join(tmp_library.libdir, name)
    os.makedirs(folder)
    if nfiles:
        data = dict(data)
        data["files"] = [os.path.basename(create_random_file(dir=folder))
                         for _ in range(nfiles)]

    document = Document(folder, data)
    document[ID_KEY_NAME] = compute_an_id(document)
    document.save()


def test_explore_citations(tmp_library: TemporaryLibrary) -> None:
    """The citations command transforms the chain contents (the document has
    no citations, so the result is empty)."""
    data = _explore_export(
        tmp_library, ["lib", "-q", "krishnamurti", "citations"],
        "citations_out.json")

    assert data == []


def test_explore_citations_reads_files(tmp_library: TemporaryLibrary) -> None:
    """The citations of the documents in a library are read from their citation
    files and deduplicated across documents: the second one repeats a citation
    of the first one."""
    import papis.database
    from papis.citations import save_citations
    from papis.document import from_folder

    _make_library_document(tmp_library, "citing_a",
                           {"title": "Citing A", "author": "A", "year": 2000})
    _make_library_document(tmp_library, "citing_b",
                           {"title": "Citing B", "author": "B", "year": 2001})
    db = papis.database.get()
    db.clear()
    db.initialize()

    save_citations(from_folder(os.path.join(tmp_library.libdir, "citing_a")), [
        {"doi": "10.1000/cited-once", "title": "Cited once"},
        {"doi": "10.1000/cited-twice", "title": "Cited twice"},
    ])
    save_citations(from_folder(os.path.join(tmp_library.libdir, "citing_b")), [
        {"doi": "10.1000/CITED-TWICE", "title": "Cited twice"},
        {"doi": "10.1000/cited-last", "title": "Cited last"},
    ])

    data = _explore_export(
        tmp_library,
        ["lib", "-q", papis.database.get_all_query_string(), "citations"],
        "citations_out.json")

    assert len(data) == 3
    # NOTE: either case variant of the repeated DOI can win the deduplication
    # depending on the order in which the library folders are visited
    assert sorted(str(d["doi"]).lower() for d in data) == [
        "10.1000/cited-last",
        "10.1000/cited-once",
        "10.1000/cited-twice",
    ]


def test_explore_add_keeps_files(tmp_library: TemporaryLibrary) -> None:
    """A document taken from a library keeps its files when added to another one
    (the chain has to preserve the document folder to resolve them)."""
    import papis.database
    from papis.commands.explore import cli
    from papis.document import from_folder

    _make_library_document(tmp_library, "source_doc",
                           {"title": "Zzsource", "author": "Nobody"}, nfiles=1)

    db = papis.database.get()
    db.clear()
    db.initialize()
    folders = {d.get_main_folder() for d in db.get_all_documents()}

    result = PapisRunner().invoke(cli, ["lib", "-q", "Zzsource", "add"])
    assert result.exit_code == 0

    new_folder, = {d.get_main_folder() for d in db.get_all_documents()} - folders
    assert new_folder is not None

    added = from_folder(new_folder)
    assert added.get_files()
    assert all(os.path.exists(f) for f in added.get_files())


def test_explore_cmd_batch(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.explore import cli

    result = PapisRunner().invoke(
        cli, ["lib", "-q", "krishnamurti",
              "cmd", "--batch", "sh -c 'exit 1'"])
    assert result.exit_code == 0
