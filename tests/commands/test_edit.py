import os
import pytest

import papis.database

from tests.testlib import TemporaryLibrary, PapisRunner


@pytest.mark.library_setup(settings={
    "editor": "python {}".format(__file__),
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
    "editor": "echo",
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
    result = cli_runner.invoke(
        cli,
        ["--all", "--editor", "ls", "krishnamurti"])
    assert result.exit_code == 0
    assert papis.config.get("editor") == "ls"

    # check --notes
    notes_name = papis.config.get("notes-name")
    assert notes_name

    result = cli_runner.invoke(
        cli,
        ["--all", "--editor", "echo", "--notes", "krishnamurti"])
    assert result.exit_code == 0
    assert papis.config.get("editor") == "echo"

    db = papis.database.get()
    doc, = db.query_dict({"author": "Krishnamurti"})
    folder = doc.get_main_folder()
    assert folder is not None

    expected_notes_path = os.path.join(folder, notes_name)
    assert os.path.exists(expected_notes_path)


def sed_replace(filename: str) -> None:
    # NOTE: this function is used by 'test_edit_run' to provide a cross-platform
    # way to edit a file that the test can later recognize and see it was called
    with open(filename) as fd:
        contents = "\n".join([
            line.replace("title: ", "title: test_edit") for line in fd
            ])

    with open(filename, "w") as fd:
        fd.write(contents)


if __name__ == "__main__":
    import sys
    sed_replace(sys.argv[-1])
