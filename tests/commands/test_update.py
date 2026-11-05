from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import pytest

import papis.database
from papis.testing import (
    PapisRunner,
    ResourceCache,
    TemporaryLibrary,
    make_lookup_handler,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from papis.document import Document, DocumentLike
    from papis.sources.handler import LookupInput
    from papis.sources.lookup import LookupResult


def _get_resource_file(filename: str) -> str:
    resources = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "resources", "update"
    )
    filepath = os.path.join(resources, filename)
    assert os.path.exists(filepath)

    return filepath


def _update_doc_from_data_interactively(
    document: Document, data: DocumentLike, data_name: str
) -> None:
    document.update(data)


def _sha256sum(path: str, chunksize: int = 8192) -> str:
    import hashlib

    hash = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunksize), b""):
            hash.update(chunk)

    return hash.hexdigest()


def test_update_run(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import run

    db = papis.database.get()
    docs = db.get_all_documents()
    doc = docs[0]

    expected_doc = docs[0]
    expected_doc["tags"] = ["test_tag"]

    tags = "test_tag"
    run(doc, data={"tags": tags})

    (doc,) = db.query_dict({"tags": tags})
    assert doc == expected_doc


def test_update_set_general_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    # check --set multiple values
    result = cli_runner.invoke(
        cli, [
            "--set", "doi", "10.213.phys.rev/213",
            "--set", "ref", "NewRef",
            "--set", "year", "1234",
            "--set", "author_list", "[{'family': 'Krishnamurti', 'given': 'J.'}]",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["doi"] == "10.213.phys.rev/213"
    assert doc["ref"] == "NewRef"
    assert doc["year"] == 1234
    assert doc["author_list"] == [{"family": "Krishnamurti", "given": "J."}]

    # check --set multiple values to the same key
    result = cli_runner.invoke(
        cli, [
            "--set", "ref", "NewRef",
            "--set", "ref", "NewerRef",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["ref"] == "NewerRef"


def test_update_set_clean_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    # check --set cleans up file names
    result = cli_runner.invoke(
        cli, [
            "--set", "notes", "a note $ to be cleaned.md",
            "--set", "files", "['file 1.pdf', 'file @.epub']",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["notes"] == "a-note-to-be-cleaned.md"
    assert doc["files"] == ["file-1.pdf", "file-.epub"]


def test_update_set_force_str_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    # check --set converts to string for known keys
    result = cli_runner.invoke(
        cli, [
            "--set", "title", "1234",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["title"] == "1234"


def test_update_set_list_item(
    tmp_library: TemporaryLibrary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import papis.tui.utils
    from papis.commands.update import cli

    monkeypatch.setattr(papis.tui.utils, "confirm", lambda *args: False)

    db = papis.database.get()
    cli_runner = PapisRunner()

    # check --set valid list item
    result = cli_runner.invoke(
        cli,
        ["--set", "tags", "1:4321", "krishnamurti"],
    )
    assert result.exit_code == 0

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["tags"] == ["tag1", 4321]

    # check --set out of bounds
    result = cli_runner.invoke(
        cli,
        ["--set", "tags", "7:4321", "krishnamurti"],
    )
    assert result.exit_code == 1

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["tags"] == ["tag1", 4321]

    # check --set non-list key
    result = cli_runner.invoke(
        cli,
        ["--set", "funkykey", "['funkyvalue']",
         "--set", "funkykey", "0:othervalue",
         "krishnamurti"],
    )
    assert result.exit_code == 0

    # NOTE: we do not expect that "funkykey" is a list, so we treat the --set
    # as a normal set instead and overwrite the list with a string
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["funkykey"] == "0:othervalue"


def test_update_append_general_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    # check --append to a string value
    result = cli_runner.invoke(
        cli, [
            "--append", "title", "appended",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["title"] == "Freedom from the knownappended"


def test_update_append_to_new_key_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    # check --append to non-existent key with known type
    result = cli_runner.invoke(
        cli, [
            "--append", "notes", "a-note.md",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["notes"] == "a-note.md"


def test_update_append_to_int_cli(
    tmp_library: TemporaryLibrary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import papis.tui.utils
    from papis.commands.update import cli

    monkeypatch.setattr(papis.tui.utils, "confirm", lambda *args: False)

    db = papis.database.get()
    cli_runner = PapisRunner()

    # check --append to unsupported value
    result = cli_runner.invoke(
        cli, [
            "--append", "year", "123",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 1

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["year"] == 2009


def test_update_append_str_to_empty_int_cli(
    tmp_library: TemporaryLibrary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import papis.tui.utils
    from papis.commands.update import cli

    monkeypatch.setattr(papis.tui.utils, "confirm", lambda *args: False)

    db = papis.database.get()
    cli_runner = PapisRunner()

    # check --append to non-existent key with known type
    result = cli_runner.invoke(
        cli, [
            "--append", "year", "string",
            "popper"
        ],
    )
    assert result.exit_code == 1

    (doc,) = db.query_dict({"author": "popper"})
    assert "year" not in doc


def test_update_append_clean_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    # check --append cleanup
    result = cli_runner.invoke(
        cli, ["--append", "files", "some file name.pdf", "krishnamurti"]
    )
    assert result.exit_code == 0

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert "some-file-name.pdf" in doc["files"]


def test_update_append_del_duplicates_in_list_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    nfiles = len(doc["files"])

    # check --append multiple items to same key
    result = cli_runner.invoke(
        cli, [
            "--append", "files", "file1.pdf",
            "--append", "files", "file1.pdf",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["files"].count("file1.pdf") == 1
    assert len(doc["files"]) == nfiles + 1


def test_update_remove_general_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    # check --remove all items from a list
    result = cli_runner.invoke(
        cli, [
            "--remove", "tags", "tag1",
            "--remove", "tags", "1234",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc.get("tags") is None


def test_update_remove_from_missing_key_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    # check --remove missing key and then --remove existing key
    result = cli_runner.invoke(
        cli, [
            # NOTE: --batch makes it ignore the missingkey and pass through
            "--batch",
            "--remove", "missingkey", "value",
            "--remove", "tags", "tag1",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 1

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["tags"] == [1234]


def test_update_remove_from_str_cli(
    tmp_library: TemporaryLibrary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import papis.tui.utils
    from papis.commands.update import cli

    monkeypatch.setattr(papis.tui.utils, "confirm", lambda *args: False)

    db = papis.database.get()
    cli_runner = PapisRunner()

    # check --remove from unsupported key type
    result = cli_runner.invoke(
        cli,
        ["--remove", "title", "known", "krishnamurti"],
    )
    assert result.exit_code == 1

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["title"] == "Freedom from the known"


def test_update_drop_general_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    # check --drop existing key
    result = cli_runner.invoke(
        cli,
        ["--drop", "title", "krishnamurti"],
    )
    assert result.exit_code == 0

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc.get("title") is None


def test_update_drop_missing_key_cli(
    tmp_library: TemporaryLibrary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import papis.tui.utils
    from papis.commands.update import cli

    monkeypatch.setattr(papis.tui.utils, "confirm", lambda *args: False)

    cli_runner = PapisRunner()

    # check --drop non-existing key
    result = cli_runner.invoke(
        cli,
        ["--drop", "notes", "krishnamurti"],
    )
    assert result.exit_code == 1


def test_update_drop_batch_cli(
    tmp_library: TemporaryLibrary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import papis.tui.utils
    from papis.commands.update import cli

    monkeypatch.setattr(papis.tui.utils, "confirm", lambda *args: False)

    db = papis.database.get()
    cli_runner = PapisRunner()

    # check --drop of a missing key without --batch prompts and exits 1
    result = cli_runner.invoke(
        cli,
        ["--drop", "notes", "krishnamurti"],
    )
    assert result.exit_code == 1

    # check --drop of a missing key with --batch skips the error and exits 1
    result = cli_runner.invoke(
        cli,
        ["--batch", "--drop", "notes", "krishnamurti"],
    )
    assert result.exit_code == 1

    # check that --batch skips a failing --drop but still applies subsequent ops
    result = cli_runner.invoke(
        cli, [
            "--batch",
            "--drop", "notes",   # notes doesn't exist: skipped
            "--drop", "tags",    # tags exists: should be applied
            "krishnamurti"
        ],
    )
    assert result.exit_code == 1

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc.get("tags") is None


def test_update_reset_batch_cli(
    tmp_library: TemporaryLibrary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import papis.config
    import papis.tui.utils

    monkeypatch.setattr(papis.tui.utils, "confirm", lambda *args: False)

    papis.config.set("ref-format", "test-{doc[author]}-{doc[year]}")

    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    # check --reset of an unsupported key without --batch exits 1
    result = cli_runner.invoke(
        cli,
        ["--reset", "title", "krishnamurti"],
    )
    assert result.exit_code == 1

    (doc,) = db.query_dict({"author": "Krishnamurti"})

    # check --reset of an unsupported key with --batch skips and exits 1
    result = cli_runner.invoke(
        cli,
        ["--batch", "--reset", "title", "krishnamurti"],
    )
    assert result.exit_code == 1

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc.get("title") == "Freedom from the known"


def test_update_reset_cli(
    tmp_library: TemporaryLibrary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import papis.config
    import papis.tui.utils

    monkeypatch.setattr(papis.tui.utils, "confirm", lambda *args: False)

    papis.config.set("ref-format", "test-{doc[author]}-{doc[year]}")
    papis.config.set("add-file-name", "test - {doc[year]} - {doc[author]}")
    papis.config.set("multiple-authors-format", "{au[given]} {au[family]} Jr.")

    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    (doc,) = db.query_dict({"author": "Scott"})
    assert doc["ref"] == "scott2008that"

    folder = doc.get_main_folder()
    orig_filename, = doc.get_files()
    _, ext = os.path.splitext(orig_filename)
    assert os.path.exists(orig_filename)
    assert folder is not None

    # check invalid key reset
    result = cli_runner.invoke(
        cli,
        ["--reset", "missingkey", "scott"])
    assert result.exit_code == 1

    result = cli_runner.invoke(
        cli,
        ["--reset", "booktitle", "scott"])
    assert result.exit_code == 1

    # check refs get reset
    expected_ref = "test_Scott_Michael_2008"
    result = cli_runner.invoke(
        cli,
        ["--reset", "ref", "scott"])
    assert result.exit_code == 0

    (doc,) = db.query_dict({"author": "Scott"})
    assert doc["ref"] == expected_ref

    # check files get reset
    expected_filename = f"test-2008-scott-michael{ext}"
    result = cli_runner.invoke(
        cli,
        ["--reset", "files", "scott"])
    assert result.exit_code == 0

    (doc,) = db.query_dict({"author": "Scott"})
    assert doc["files"] == [expected_filename]
    assert os.path.exists(os.path.join(folder, expected_filename))
    assert not os.path.exists(orig_filename)

    # check author gets reset
    result = cli_runner.invoke(
        cli,
        ["--reset", "author", "scott"])
    assert result.exit_code == 0

    (doc,) = db.query_dict({"author": "Scott"})
    assert doc["author"] == "Michael Scott Jr."


@pytest.mark.library_setup(filetype="pdf")
def test_update_set_files_renames_on_disk(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    (doc,) = db.query_dict({"author": "scott"})
    folder = doc.get_main_folder()
    assert folder is not None

    orig_filename, = doc["files"]
    orig_path = os.path.join(folder, orig_filename)
    assert os.path.exists(orig_path)

    new_filename = "renamed-by-set.pdf"
    new_path = os.path.join(folder, new_filename)

    # set the first (and only) file to a new name using the list-index syntax
    result = cli_runner.invoke(
        cli,
        ["--set", "files", f"0:{new_filename}", "scott"],
    )
    assert result.exit_code == 0

    # the old file should be gone and the new one should be in its place
    assert not os.path.exists(orig_path)
    assert os.path.exists(new_path)

    # the metadata should reflect the rename
    (doc,) = db.query_dict({"author": "scott"})
    assert doc["files"] == [new_filename]


@pytest.mark.library_setup(filetype="pdf")
def test_update_reset_many_files_cli(tmp_library: TemporaryLibrary) -> None:
    import papis.config
    from papis.commands.addto import run as addto

    db = papis.database.get()
    papis.config.set("add-file-name", "{doc[author]}-{doc[title]}")

    (doc,) = db.query_dict({"author": "scott"})

    # NOTE: the files in this document will now be
    #  0:some-randomly-generated-thing.ext
    #  1:add-file-name.pdf
    #  2:add-file-name-a.pdf
    #  3:add-file-name-b.pdf
    # Therefore, when trying to rename them, the files would overlap if done naively
    addto(doc, [tmp_library.create_random_file("pdf") for _ in range(3)])
    checksums = [_sha256sum(filename) for filename in doc.get_files()]

    from papis.commands.update import cli

    cli_runner = PapisRunner()

    # check --reset for many files to make sure that they are not overwritten
    result = cli_runner.invoke(
        cli,
        ["--reset", "files", "scott"])
    assert result.exit_code == 0

    (doc,) = db.query_dict({"author": "scott"})
    assert len(doc["files"]) == 4
    assert [_sha256sum(filename) for filename in doc.get_files()] == checksums


def test_update_rename_general_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    # check --rename known keys with valid values
    result = cli_runner.invoke(
        cli, [
            "--rename", "tags", "tag1", "tag_renamed1",
            "--rename", "tags", "1234", "2345",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["tags"] == ["tag_renamed1", 2345]


def test_update_rename_missing_value_cli(
    tmp_library: TemporaryLibrary,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import papis.tui.utils
    from papis.commands.update import cli

    monkeypatch.setattr(papis.tui.utils, "confirm", lambda *args: False)

    cli_runner = PapisRunner()

    # check --rename non-existent key value
    result = cli_runner.invoke(
        cli, [
            "--rename", "tags", "tag_nonexistent", "tag_renamed1",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 1


def test_update_batch_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    # check --batch in a series of operations
    result = cli_runner.invoke(
        cli, [
            "--batch",
            "--append", "year", "123",      # this fails
            "--remove", "year", "123",      # this fails
            "--append", "tags", "tag3",     # but this should still work
            "krishnamurti"
        ],
    )
    assert result.exit_code == 1

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert "tag3" in doc["tags"]


def test_update_batch_same_key_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    # check that --batch applies the successful operations even if another
    # operation on the same key fails
    result = cli_runner.invoke(
        cli, [
            "--batch",
            "--remove", "tags", "tag_nonexistent",   # this fails
            "--append", "tags", "philosophy",        # but this should still work
            "krishnamurti"
        ],
    )
    assert result.exit_code == 1

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert "philosophy" in doc["tags"]
    assert "tag_nonexistent" not in doc["tags"]


def test_update_append_idempotent_cli(
    tmp_library: TemporaryLibrary,
    caplog: pytest.LogCaptureFixture,
) -> None:
    import logging
    caplog.set_level(logging.INFO)

    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    # appending a value that is already present is a no-op and should be
    # reported as such, rather than counting as an "updated" document
    result = cli_runner.invoke(
        cli, [
            "--append", "tags", "tag1", "krishnamurti",
        ],
    )
    assert result.exit_code == 0

    messages = [r.message for r in caplog.records]
    assert any("Updated 1 / 1 documents." in msg for msg in messages)

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["tags"] == ["tag1", 1234]


def test_update_yaml_cli(
    tmp_library: TemporaryLibrary,
    resource_cache: ResourceCache,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import papis.utils
    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    filename = os.path.join(resource_cache.cachedir, "update", "russell.yaml")

    with monkeypatch.context() as m:
        m.setattr(
            papis.utils,
            "update_doc_from_data_interactively",
            _update_doc_from_data_interactively,
        )

        result = cli_runner.invoke(cli, ["--from", "yaml", filename, "krishnamurti"])
        assert result.exit_code == 0

    from papis.yaml import yaml_to_data

    data = yaml_to_data(filename)

    (doc,) = db.query_dict({"author": "Russell"})
    assert doc["doi"] == data["doi"]


def test_update_bibtex_cli(
    tmp_library: TemporaryLibrary,
    resource_cache: ResourceCache,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import papis.utils
    from papis.commands.update import cli

    db = papis.database.get()
    cli_runner = PapisRunner()

    filename = os.path.join(resource_cache.cachedir, "update", "wannier.bib")

    with monkeypatch.context() as m:
        m.setattr(
            papis.utils,
            "update_doc_from_data_interactively",
            _update_doc_from_data_interactively,
        )

        result = cli_runner.invoke(cli, ["--from", "bibtex", filename, "krishnamurti"])
        assert result.exit_code == 0

    from papis.bibtex import bibtex_to_dict

    with open(filename, encoding="utf-8") as fd:
        (data,) = bibtex_to_dict(fd.read())

    (doc,) = db.query_dict({"author": "Wannier"})
    assert doc["doi"] == data["doi"]


def test_update_from_sources_looks_up_per_document(
    tmp_library: TemporaryLibrary,
    monkeypatch: pytest.MonkeyPatch,
    handler_registry: Callable[..., None],
) -> None:
    """'--from' is looked up once per document, like the legacy importers."""
    import papis.sources.lookup
    from papis.commands.update import cli

    cli_runner = PapisRunner()
    handler_registry(make_lookup_handler("fake", document={"title": "New title"}))

    real_lookup = papis.sources.lookup.lookup
    calls: list[LookupInput] = []

    def _counting_lookup(
            evidence: LookupInput, *,
            sources: list[str] | None = None) -> list[LookupResult]:
        calls.append(evidence)
        return real_lookup(evidence, sources=sources)

    # NOTE: patch the name as the client module bound it ('lookup_item' calls it)
    monkeypatch.setattr("papis.sources.client.lookup", _counting_lookup)

    ndocs = len(papis.database.get().get_all_documents())
    assert ndocs > 1

    result = cli_runner.invoke(
        cli, ["-a", "--batch", "--from", "fake", "some-input"])
    assert result.exit_code == 0

    # NOTE: '--from' evidence is document-independent, but it is fetched for
    # every document (legacy importer flow), not once for all of them
    assert len(calls) == ndocs


def test_update_interactive_keeps_user_changes_cli(
    tmp_library: TemporaryLibrary,
    monkeypatch: pytest.MonkeyPatch,
    handler_registry: Callable[..., None],
) -> None:
    """Interactive merging never overwrites user changes silently."""
    import papis.utils
    from papis.commands.update import cli

    db = papis.database.get()
    handler_registry(make_lookup_handler(
        "fake", document={"title": "Source title", "marker": "from-source"}))

    merged: list[str] = []

    def _reject(document: Document, data: DocumentLike, data_name: str) -> None:
        merged.append(data_name)

    monkeypatch.setattr(
        papis.utils, "update_doc_from_data_interactively", _reject)

    cli_runner = PapisRunner()
    result = cli_runner.invoke(
        cli, ["--auto", "--set", "title", "User title", "krishnamurti"])
    assert result.exit_code == 0

    # the user resolved the merge for the source's data, and their choice stands
    assert merged == ["fake"]

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["title"] == "User title"
    assert "marker" not in doc


def test_update_from_no_source_picker_cli(
        tmp_library: TemporaryLibrary,
        monkeypatch: pytest.MonkeyPatch,
        handler_registry: Any,
        ) -> None:
    """Explicit '--from' results merge in command-line order without selection."""
    import papis.tui.utils
    import papis.utils
    from papis.commands.update import cli

    handler_registry(
        make_lookup_handler("fake-a", document={"title": "A-title", "a": "A"}),
        make_lookup_handler("fake-b", document={"title": "B-title", "b": "B"}))

    def _fail(options: Any, message: str, **kwargs: Any) -> list[int]:
        raise AssertionError("'--from' results must not be offered for selection")

    offered: list[str] = []

    def _record(doc: Any, data: Any, name: str) -> None:
        offered.append(name)
        doc.update(data)

    monkeypatch.setattr(papis.tui.utils, "select_range", _fail)
    monkeypatch.setattr(papis.utils, "update_doc_from_data_interactively", _record)

    cli_runner = PapisRunner()
    result = cli_runner.invoke(
        cli, ["--from", "fake-a", "x", "--from", "fake-b", "y", "krishnamurti"])
    assert result.exit_code == 0

    # with the document data as base nothing merges silently
    assert offered == ["fake-a", "fake-b"]

    db = papis.database.get()
    doc, = db.query_dict({"author": "Krishnamurti"})

    # the later '--from' pair wins the conflicting key
    assert doc["title"] == "B-title"
    assert doc["a"] == "A"
    assert doc["b"] == "B"


def test_update_auto_picker_cli(
        tmp_library: TemporaryLibrary,
        monkeypatch: pytest.MonkeyPatch,
        handler_registry: Any,
        ) -> None:
    """'--auto' results are inferred guesses: the user picks the sources."""
    import papis.tui.utils
    import papis.utils
    from papis.commands.update import cli

    handler_registry(
        make_lookup_handler("fake-a", document={"title": "A-title", "a": "A"}),
        make_lookup_handler("fake-b", document={"title": "B-title", "b": "B"}))

    options: list[str] = []

    def _select(candidates: list[str], message: str, **kwargs: Any) -> list[int]:
        options.extend(candidates)
        return [0]

    monkeypatch.setattr(papis.tui.utils, "select_range", _select)
    monkeypatch.setattr(
        papis.utils, "update_doc_from_data_interactively",
        _update_doc_from_data_interactively)
    monkeypatch.setattr(
        "papis.document.describe", lambda document: document["title"])

    cli_runner = PapisRunner()
    result = cli_runner.invoke(cli, ["--auto", "krishnamurti"])
    assert result.exit_code == 0

    assert options == [
        "[fake-a] A-title (files: none)",
        "[fake-b] B-title (files: none)",
    ]

    db = papis.database.get()
    doc, = db.query_dict({"author": "Krishnamurti"})

    # the deselected source contributes nothing
    assert doc["title"] == "A-title"
    assert doc["a"] == "A"
    assert "b" not in doc


def test_update_from_and_auto_cli(
        tmp_library: TemporaryLibrary,
        monkeypatch: pytest.MonkeyPatch,
        handler_registry: Any,
        ) -> None:
    """'--from' and '--auto' combine as in 'papis add': both are looked up and
    the explicit '--from' data wins, without being offered for selection."""
    import papis.tui.utils
    import papis.utils
    from papis.commands.update import cli

    handler_registry(
        make_lookup_handler(
            "fake-auto", document={"title": "auto-title", "auto": "A"}),
        make_lookup_handler(
            "fake-from", document={"title": "from-title", "from": "F"}))

    offered: list[str] = []

    def _select(candidates: list[str], message: str, **kwargs: Any) -> list[int]:
        offered.extend(candidates)
        return [0]

    monkeypatch.setattr(papis.tui.utils, "select_range", _select)
    monkeypatch.setattr(
        papis.utils, "update_doc_from_data_interactively",
        _update_doc_from_data_interactively)
    monkeypatch.setattr(
        "papis.document.describe", lambda document: document["title"])

    cli_runner = PapisRunner()
    result = cli_runner.invoke(
        cli, ["--auto", "--from", "fake-from", "x", "krishnamurti"])
    assert result.exit_code == 0

    # NOTE: the '--auto' fan-out matches every source, including the pinned one,
    #   so both appear for selection (as with fan-out in 'papis add'); the
    #   explicit result itself is never offered for selection
    assert offered == [
        "[fake-auto] auto-title (files: none)",
        "[fake-from] from-title (files: none)",
    ]

    db = papis.database.get()
    doc, = db.query_dict({"author": "Krishnamurti"})

    # both sources contribute, the explicit one wins the conflict
    assert doc["auto"] == "A"
    assert doc["from"] == "F"
    assert doc["title"] == "from-title"


def test_update_auto_cli(tmp_library: TemporaryLibrary,
                         handler_registry: Callable[..., None],
                         ) -> None:
    """``--auto`` merges importer data without fetching any files."""
    from papis.commands.update import cli

    db = papis.database.get()
    doc, = db.query_dict({"author": "krishnamurti"})
    files_before = doc.get_files()

    cli_runner = PapisRunner()
    handler_registry(make_lookup_handler(
        "fake",
        document={"title": "New title", "year": 2020},
        files=["/path/that/does/not/exist.pdf"]))

    result = cli_runner.invoke(
        cli, ["--auto", "--batch", "krishnamurti"])
    assert result.exit_code == 0

    doc, = db.query_dict({"author": "krishnamurti"})

    assert doc["title"] == "New title"
    assert doc["year"] == 2020
    assert doc["author"] == "J. Krishnamurti"

    assert doc.get_files() == files_before


def test_update_auto_unchanged_cli(tmp_library: TemporaryLibrary,
                                   monkeypatch: pytest.MonkeyPatch,
                                   handler_registry: Callable[..., None],
                                   ) -> None:
    """No document rewrite if ``--auto`` provides only existing values."""
    import papis.commands.update
    from papis.commands.update import cli

    cli_runner = PapisRunner()
    db = papis.database.get()
    doc, = db.query_dict({"author": "krishnamurti"})

    handler_registry(make_lookup_handler(
        "fake",
        document={"title": doc["title"], "year": doc["year"]},
        files=["/path/that/does/not/exist.pdf"]))

    calls: list[tuple[object, ...]] = []
    monkeypatch.setattr(papis.commands.update, "run",
                        lambda *args, **kwargs: calls.append(args))

    result = cli_runner.invoke(
        cli, ["--auto", "--batch", "krishnamurti"])
    assert result.exit_code == 0
    assert calls == []


def test_update_source_error_warns(
    tmp_library: TemporaryLibrary,
    handler_registry: Callable[..., None],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A failed source is warned about and does not abort the command."""
    from papis.commands.update import cli
    from papis.exceptions import SourceError

    cli_runner = PapisRunner()
    handler_registry(make_lookup_handler("fake", lookup_exc=SourceError("boom")))

    with caplog.at_level("WARNING"):
        result = cli_runner.invoke(cli, ["--auto", "--batch", "krishnamurti"])

    assert result.exit_code == 0
    assert "fake" in caplog.text
    assert "boom" in caplog.text


def test_update_auto_preserves_underscore_files_and_notes(
    tmp_library: TemporaryLibrary,
    handler_registry: Callable[..., None],
) -> None:
    """An update must not rewrite (normalize/rename) unchanged files or notes."""
    from papis.commands.update import cli
    from papis.database import get

    db = get()
    doc, = db.query_dict({"author": "krishnamurti"})
    folder = doc.get_main_folder()
    assert folder is not None

    old = doc["files"][0]
    basename, ext = os.path.splitext(old)
    filename = f"{basename}_x{ext}"
    os.replace(os.path.join(folder, old), os.path.join(folder, filename))
    doc["files"] = [filename]

    notes = "My_Notes.TEX"
    with open(os.path.join(folder, notes), "w", encoding="utf-8") as fd:
        fd.write("% notes\n")

    doc["notes"] = notes
    doc.save()
    db.update(doc)

    handler_registry(make_lookup_handler(
        "fake",
        document={"title": "New title", "year": 2020},
        files=["/nonexistent.pdf"]))

    result = PapisRunner().invoke(cli, ["--auto", "--batch", "krishnamurti"])
    assert result.exit_code == 0

    doc, = db.query_dict({"author": "krishnamurti"})
    assert doc["files"] == [filename]
    assert doc.get_files() == [os.path.join(folder, filename)]

    assert doc["notes"] == notes
    assert os.path.exists(os.path.join(folder, notes))
    assert not os.path.exists(os.path.join(folder, "my-notes.tex"))


def test_update_auto_evidence_fields_are_text(
    tmp_library: TemporaryLibrary,
    monkeypatch: pytest.MonkeyPatch,
    handler_registry: Callable[..., None],
) -> None:
    """``--auto`` hands the handlers text: a document's lists (authors, tags) and
    missing values are not identifiers."""
    import papis.sources.lookup as lookup_module
    from papis.commands.update import cli

    handler_registry(make_lookup_handler("fake", document={"title": "Source title"}))

    captured: list[LookupInput] = []
    real_lookup = lookup_module.lookup

    def _capture(
        evidence: LookupInput, *, sources: list[str] | None = None
    ) -> list[LookupResult]:
        captured.append(evidence)
        return real_lookup(evidence, sources=sources)

    # NOTE: the command imports the name when it runs, so patching it on its
    # module is enough
    monkeypatch.setattr(lookup_module, "lookup", _capture)

    cli_runner = PapisRunner()
    assert cli_runner.invoke(cli, ["--auto", "--batch", "krishnamurti"]).exit_code == 0

    assert captured
    for evidence in captured:
        assert all(isinstance(value, str) for value in evidence.fields.values())
