import os
import pytest
import shutil
from _pytest.monkeypatch import MonkeyPatch

import papis.database

from papis.testing import TemporaryLibrary, PapisRunner


def test_rm_run(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.rm import run

    db = papis.database.get()
    docs = db.get_all_documents()
    folder = docs[0].get_main_folder()
    assert os.path.exists(folder)

    run(docs[0])
    assert not os.path.exists(folder)


@pytest.mark.skipif(
    not shutil.which("git"),
    reason="Test requires 'git' executable to be in the PATH")
@pytest.mark.library_setup(use_git=True)
def test_rm_files_run(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.rm import run

    db = papis.database.get()
    docs = db.get_all_documents()
    doc = next(doc for doc in docs if "files" in doc)
    assert "files" in doc

    title = doc["title"]
    filename = doc.get_files()[0]
    assert os.path.exists(filename)

    run(doc, filepath=filename, git=True)
    assert not os.path.exists(filename)

    db.clear()
    db.initialize()

    doc, = db.query_dict({"title": title})
    assert doc["title"] == title
    assert filename not in doc.get_files()


def test_rm_cli(tmp_library: TemporaryLibrary, monkeypatch: MonkeyPatch) -> None:
    import papis.tui.utils
    from papis.commands.rm import cli
    cli_runner = PapisRunner()

    db = papis.database.get()
    doc, = db.query_dict({"author": "turing"})
    folder = doc.get_main_folder()
    assert os.path.exists(folder)

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "text_area", lambda *args, **kwargs: None)
        m.setattr(papis.tui.utils, "confirm", lambda *args: True)

        result = cli_runner.invoke(
            cli,
            ["__no_document__"])
        assert result.exit_code == 0

        result = cli_runner.invoke(
            cli,
            ["turing"])
        assert result.exit_code == 0
        assert not os.path.exists(folder)

        result = cli_runner.invoke(
            cli,
            ["krishnamurti"])
        assert result.exit_code == 0

    docs = db.query_dict({"author": "krishnamurti"})
    assert not docs


def test_rm_all_cli(tmp_library: TemporaryLibrary, monkeypatch: MonkeyPatch) -> None:
    import papis.tui.utils
    from papis.commands.rm import cli
    cli_runner = PapisRunner()
    db = papis.database.get()

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "confirm", lambda *args: True)

        result = cli_runner.invoke(
            cli,
            ["--all", "--force", "test_author"])
        assert result.exit_code == 0

    docs = db.query_dict({"author": "test_author"})
    assert not docs


@pytest.mark.parametrize("confirm", [True, False])
def test_rm_confirm_cli(tmp_library: TemporaryLibrary,
                        monkeypatch: MonkeyPatch,
                        confirm: bool) -> None:
    import papis.tui.utils
    from papis.commands.rm import cli
    cli_runner = PapisRunner()

    db = papis.database.get()
    doc, = db.query_dict({"author": "krishnamurti"})
    folder = doc.get_main_folder()
    assert os.path.exists(folder)

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "text_area", lambda *args, **kwargs: None)
        m.setattr(papis.tui.utils, "confirm", lambda *args: confirm)

        result = cli_runner.invoke(
            cli,
            ["krishnamurti"])
        assert result.exit_code == 0
        assert os.path.exists(folder) == (not confirm)

    docs = db.query_dict({"author": "krishnamurti"})
    assert bool(docs) == (not confirm)


@pytest.mark.parametrize("confirm", [True, False])
@pytest.mark.parametrize("pick", [True, False])
def test_rm_files_cli(tmp_library: TemporaryLibrary,
                      monkeypatch: MonkeyPatch,
                      confirm: bool, pick: bool) -> None:
    import papis.pick
    import papis.tui.utils

    from papis.commands.rm import cli
    cli_runner = PapisRunner()

    db = papis.database.get()
    doc, = db.query_dict({"author": "krishnamurti"})
    filename, = doc.get_files()
    assert os.path.exists(filename)

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "confirm", lambda *args, **kwargs: confirm)
        m.setattr(papis.pick, "pick", lambda x, **k: [x[0]] if (x and pick) else [])

        result = cli_runner.invoke(
            cli,
            ["--file", "krishnamurti"])
        assert result.exit_code == 0
        assert os.path.exists(filename) == (not confirm or not pick)

    doc, = db.query_dict({"author": "krishnamurti"})
    assert bool(doc.get_files()) == (not confirm or not pick)
