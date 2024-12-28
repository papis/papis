import os

import papis.database

from papis.testing import TemporaryLibrary, PapisRunner


def _get_resource_file(filename: str) -> str:
    resources = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "resources", "update"
    )
    filepath = os.path.join(resources, filename)
    assert os.path.exists(filepath)

    return filepath


def test_tag_add_general_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.tag import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli, [
            "--add", "tag3",
            "--add", "2345",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert "tag1" in doc["tags"]
    assert 2345 in doc["tags"]


def test_tag_add_to_new_key_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.tag import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli,
        ["--add", "tag3", "doc without files"],
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "doc without files"})
    assert doc["tags"] == ["tag3"]


def test_tag_add_del_duplicates_in_list_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.tag import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli,
        ["--add", "tag3", "--add", "tag3", "krishnamurti"],
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc["tags"].count("tag3") == 1


def test_tag_remove_general_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.tag import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli,
        ["--remove", "tag1", "--remove", "1234", "krishnamurti"],
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc.get("tags") is None


def test_tag_remove_from_missing_key_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.tag import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli,
        ["--remove", "tag", "doc without files"],
    )
    assert result.exit_code == 0


def test_tag_drop_general_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.tag import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli,
        ["--drop", "krishnamurti"],
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert doc.get("tags") is None


def test_tag_drop_missing_key_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.tag import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli,
        ["--drop", "doc without files"],
    )
    assert result.exit_code == 0


def test_tag_rename_general_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.tag import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli, [
            "--rename", "tag1", "tag_renamed1",
            "--rename", "1234", "2345",
            "krishnamurti"
        ],
    )
    assert result.exit_code == 0

    db = papis.database.get()
    (doc,) = db.query_dict({"author": "Krishnamurti"})
    assert "tag_renamed1" in doc["tags"]
    assert 2345 in doc["tags"]


def test_tag_rename_missing_value_cli(
    tmp_library: TemporaryLibrary,
) -> None:
    from papis.commands.tag import cli

    cli_runner = PapisRunner()

    result = cli_runner.invoke(cli, ["__no_document__"])
    assert result.exit_code == 0
    assert not result.output

    result = cli_runner.invoke(
        cli,
        ["--rename", "tag_nonexistent", "tag_renamed1", "krishnamurti"],
    )
    assert result.exit_code == 0
