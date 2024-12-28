import os
import pytest
from typing import Any, Dict

import papis.database
from papis.document import Document

from papis.testing import TemporaryLibrary, PapisRunner, ResourceCache


def _get_resource_file(filename: str) -> str:
    resources = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "resources", "update"
    )
    filepath = os.path.join(resources, filename)
    assert os.path.exists(filepath)

    return filepath


def update_doc_from_data_interactively(
    document: Document, data: Dict[str, Any], data_name: str
) -> None:
    document.update(data)


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

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

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

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["doi"] == "10.213.phys.rev/213"
    assert doc["ref"] == "NewRef"
    assert doc["year"] == 1234
    assert doc["author_list"] == [{"family": "Krishnamurti", "given": "J."}]


def test_update_set_clean_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli, [
            "--set", "notes", "a note $ to be cleaned.md",
            "--set", "files", "['file 1.pdf', 'file @.epub']",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["notes"] == "a-note-to-be-cleaned.md"
    assert doc["files"] == ["file-1.pdf", "file-.epub"]


def test_update_set_force_str_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli, [
            "--set", "title", "1234",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["title"] == "1234"


def test_update_append_general_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli, [
            "--append", "title", "appended",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["title"] == "Freedom from the knownappended"


def test_update_append_to_new_key_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli, [
            "--append", "notes", "a-note.md",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["notes"] == "a-note.md"


def test_update_append_to_int_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli, [
            "--append", "year", "123",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["year"] == 2009


def test_update_append_str_to_empty_int_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli, [
            "--append", "year", "string",
            "popper"
        ],
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "popper"})
    assert doc.get("year") is None


def test_update_append_clean_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli, ["--append", "files", "some file name.pdf", "krishnamurti"]
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert "some-file-name.pdf" in doc["files"]


def test_update_append_del_duplicates_in_list_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli, [
            "--append", "files", "file1.pdf",
            "--append", "files", "file1.pdf",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["files"].count("file1.pdf") == 1


def test_update_remove_general_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli, [
            "--remove", "tags", "tag1",
            "--remove", "tags", "1234",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc.get("tags") is None


def test_update_remove_from_missing_key_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli, [
            "--remove", "missingkey", "value",
            "--remove", "tags", "tag1",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["tags"] == [1234]


def test_update_remove_from_str_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli,
        ["--remove", "title", "known", "krishnamurti"],
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["title"] == "Freedom from the known"


def test_update_drop_general_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli,
        ["--drop", "title", "krishnamurti"],
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc.get("title") is None


def test_update_drop_missing_key_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli,
        ["--drop", "notes", "krishnamurti"],
    )
    assert result.exit_code == 0


def test_update_rename_general_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli, [
            "--rename", "tags", "tag1", "tag_renamed1",
            "--rename", "tags", "1234", "2345",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert "tag_renamed1" in doc["tags"]
    assert 2345 in doc["tags"]


def test_update_rename_missing_value_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli, [
            "--rename", "tags", "tag_nonexistent", "tag_renamed1",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0


def test_update_batch_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

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

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert "tag3" in doc["tags"]


def test_update_yaml_cli(
    tmp_library: TemporaryLibrary,
    resource_cache: ResourceCache,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    filename = os.path.join(resource_cache.cachedir, "update", "russell.yaml")

    import papis.utils

    with monkeypatch.context() as m:
        m.setattr(
            papis.utils,
            "update_doc_from_data_interactively",
            update_doc_from_data_interactively,
        )

        result = cli_runner.invoke(cli, ["--from", "yaml", filename, "krishnamurti"])
        assert result.exit_code == 0

    import papis.yaml

    data = papis.yaml.yaml_to_data(filename)

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Russell"})

    assert doc["doi"] == data["doi"]


def test_update_bibtex_cli(
    tmp_library: TemporaryLibrary,
    resource_cache: ResourceCache,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from papis.commands.update import cli

    cli_runner = PapisRunner()

    filename = os.path.join(resource_cache.cachedir, "update", "wannier.bib")

    import papis.utils

    with monkeypatch.context() as m:
        m.setattr(
            papis.utils,
            "update_doc_from_data_interactively",
            update_doc_from_data_interactively,
        )

        result = cli_runner.invoke(cli, ["--from", "bibtex", filename, "krishnamurti"])
        assert result.exit_code == 0

    import papis.bibtex

    (data,) = papis.bibtex.bibtex_to_dict(filename)

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Wannier"})

    assert doc["doi"] == data["doi"]
