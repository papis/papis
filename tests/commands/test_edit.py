import os

import pytest

import papis.database

from papis.testing import TemporaryLibrary, PapisRunner


def get_mock_script(name: str) -> str:
    """Constructs a command call for a command mocked by ``scripts.py``.

    :param name: the name of the command, e.g. ``ls`` or ``echo``.
    :returns: a string of the command
    """
    import sys

    script = os.path.join(os.path.dirname(__file__), "scripts.py")

    from papis.config import escape_interp

    return escape_interp(f"{sys.executable} {script} {name}")


@pytest.mark.library_setup(settings={
    "editor": get_mock_script("sed")
    })
def test_edit_run(tmp_library: TemporaryLibrary) -> None:
    import papis.config
    from papis.commands.edit import run

    print(papis.config.get("editor"))
    print(__file__)

    db = papis.database.get()
    docs = db.get_all_documents()
    run(docs[0])

    db.clear()
    db.initialize()

    doc, = db.query_dict({"title": "test_edit"})
    assert "test_edit" in doc["title"]


@pytest.mark.library_setup(settings={
    "editor": get_mock_script("echo")
    })
def test_edit_cli(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.edit import cli
    cli_runner = PapisRunner()

    # check run
    result = cli_runner.invoke(
        cli,
        ["krishnamurti"])
    assert result.exit_code == 0

    # check run with non-existent document
    result = cli_runner.invoke(
        cli,
        ["this document does not exist"])
    assert result.exit_code == 0

    # check --all
    ls = get_mock_script("ls")
    result = cli_runner.invoke(
        cli,
        ["--all", "--editor", ls, "krishnamurti"])
    assert result.exit_code == 0
    assert (papis.config.escape_interp(papis.config.get("editor"))
            == get_mock_script("ls"))

    # check --notes
    notes_name = papis.config.get("notes-name")
    assert notes_name

    result = cli_runner.invoke(
        cli,
        ["--all", "--editor", get_mock_script("echo"), "--notes", "krishnamurti"])
    assert result.exit_code == 0
    assert (papis.config.escape_interp(papis.config.get("editor"))
            == get_mock_script("echo"))

    db = papis.database.get()
    doc, = db.query_dict({"author": "Krishnamurti"})
    folder = doc.get_main_folder()
    assert folder is not None

    expected_notes_path = os.path.join(folder, notes_name)
    assert os.path.exists(expected_notes_path)
