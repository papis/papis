from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

import papis.database
from papis.testing import PapisRunner, ResourceCache, TemporaryLibrary

if TYPE_CHECKING:
    from papis.document import Document, DocumentLike


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


def test_update_set_list_item(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import cli

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


def test_update_append_to_int_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import cli

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


def test_update_append_str_to_empty_int_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import cli

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
    assert result.exit_code == 0

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["tags"] == [1234]


def test_update_remove_from_str_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.update import cli

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
) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    # check --drop non-existing key
    result = cli_runner.invoke(
        cli,
        ["--drop", "notes", "krishnamurti"],
    )
    assert result.exit_code == 1


def test_update_reset_cli(tmp_library: TemporaryLibrary) -> None:
    import papis.config
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
) -> None:
    from papis.commands.update import cli

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
    assert result.exit_code == 0

    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert "tag3" in doc["tags"]


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

    (data,) = bibtex_to_dict(filename)

    (doc,) = db.query_dict({"author": "Wannier"})
    assert doc["doi"] == data["doi"]
