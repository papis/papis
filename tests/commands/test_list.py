from __future__ import annotations

import os
from typing import TYPE_CHECKING

import papis.database
from papis.testing import PapisRunner, make_lookup_handler

if TYPE_CHECKING:
    from collections.abc import Callable

    from papis.testing import TemporaryLibrary


def test_list_run(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.list import list_documents, list_plugins

    assert papis.config.get_lib_name() == tmp_library.libname

    db = papis.database.get()
    docs = db.get_all_documents()

    objs = list_documents(docs, show_info=True)
    assert len(objs) == len(docs)
    assert all(os.path.exists(f) for f in objs)

    objs = list_documents(docs, show_notes=True)
    assert len(objs) == 0

    libs = list_plugins(show_libraries=True)
    assert len(libs) == 1

    folders = list_documents(docs, show_dir=True)
    assert len(folders) == len(docs)
    assert all(os.path.exists(f) for f in folders)

    ids = list_documents(docs, show_id=True)
    assert len(ids) == len(docs)


def test_list_sources_cli(tmp_library: TemporaryLibrary,
                            handler_registry: Callable[..., None]) -> None:
    """`papis list --sources` shows each source's capabilities (lookup,
    search with its fields, parse); internals (priority, legacy-adapter
    wrapping) are not shown. `--quiet` drops the descriptions."""
    from papis.sources.handler import ParseOutput, SearchOutput

    search = classmethod(lambda cls, evidence, *, max_results: SearchOutput())
    handler_registry(
        make_lookup_handler("fakenative", search_fields=("author", "title"),
                     search=search, __doc__="Source fakenative."),
        make_lookup_handler("fakewrapped", search_fields=("author", "title"),
                     search=search, is_legacy=True,
                     __doc__="Source fakewrapped."),
        make_lookup_handler("fakefree", search_fields=(),
                     search=search, __doc__="Source fakefree."),
        make_lookup_handler("fakeparse",
                     parse=classmethod(lambda cls, content: ParseOutput()),
                     __doc__="Source fakeparse."))

    from papis.commands.list import cli

    result = PapisRunner().invoke(cli, ["--sources"])
    assert result.exit_code == 0
    assert "fakenative" in result.output
    assert "Source fakenative." in result.output
    assert "Capabilities: lookup, search (free-text, author, title)." in result.output
    assert "fakefree" in result.output
    assert "Capabilities: lookup, search (free-text)." in result.output
    assert "fakeparse" in result.output
    assert "Capabilities: lookup, parse." in result.output
    assert "priority" not in result.output
    assert "legacy" not in result.output
    assert "folder" in result.output
    assert "lib" in result.output

    #: --quiet drops the descriptions but keeps the capabilities
    result = PapisRunner().invoke(cli, ["--sources", "--quiet"])
    assert result.exit_code == 0
    assert "Source fakenative." not in result.output
    assert "Capabilities: lookup, search (free-text, author, title)." in result.output
    assert "Capabilities: lookup, search (free-text)." in result.output
    assert "Capabilities: lookup, parse." in result.output


def test_list_downloaders_removed(tmp_library: TemporaryLibrary) -> None:
    """The legacy downloader list no longer exists."""
    from papis.commands.list import cli

    result = PapisRunner().invoke(cli, ["--downloaders"])
    assert result.exit_code != 0
    assert "No such option" in result.output
