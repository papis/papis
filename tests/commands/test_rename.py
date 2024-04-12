import os

from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch

import papis.config
import papis.database

from papis.testing import TemporaryLibrary


def test_rename_run(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.rename import run

    db = papis.database.get()
    docs = db.get_all_documents()
    doc = docs[0]

    old_title = doc["title"]
    new_name = "Some title with spaces too"

    run(doc, new_name)

    doc, = db.query_dict({"title": old_title})
    assert doc.get_main_folder_name() == new_name
    assert os.path.exists(doc.get_main_folder())


def test_folder_name_flag(tmp_library: TemporaryLibrary,
                          monkeypatch: MonkeyPatch,
                          ) -> None:
    papis.config.set("add-folder-name", "{doc[papis_id]}")

    from papis.commands.rename import cli
    from papis.testing import PapisRunner

    runner = PapisRunner()
    db = papis.database.get()

    doc, *_ = db.get_all_documents()
    papis_id = doc["papis_id"]

    old_folder_name = doc.get_main_folder()
    assert os.path.exists(old_folder_name)

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "confirm", lambda *args, **kwargs: True)

        # Check that the document will be renamed according to the default pattern
        result = runner.invoke(
            cli,
            [f"papis_id:{papis_id}"])

        doc, = db.query_dict({"papis_id": papis_id})
        assert result.exit_code == 0
        assert os.path.basename(doc.get_main_folder()) == papis_id
        assert os.path.exists(doc.get_main_folder())
        assert not os.path.exists(old_folder_name)

        # Check that we can override the default pattern
        result = runner.invoke(
            cli,
            ["--folder-name", "magicstring42", f"papis_id:{papis_id}"])

        doc, = db.query_dict({"papis_id": papis_id})
        assert result.exit_code == 0
        assert os.path.basename(doc.get_main_folder()) == "magicstring42"
        assert os.path.exists(doc.get_main_folder())


def test_rename_batch(tmp_library: TemporaryLibrary) -> None:
    papis.config.set("add-folder-name", "magic-string-42-{doc[papis_id]}")

    from papis.commands.rename import cli
    from papis.testing import PapisRunner

    runner = PapisRunner()
    runner.invoke(
        cli,
        ["--all", "--batch"])

    docs = papis.database.get().get_all_documents()
    for doc in docs:
        folder = doc.get_main_folder()

        assert os.path.exists(folder)
        assert os.path.basename(folder).startswith("magic-string-42")


def test_rename_no_matching_documents(tmp_library: TemporaryLibrary,
                                      caplog: LogCaptureFixture) -> None:
    from papis.commands.rename import cli
    from papis.testing import PapisRunner

    with caplog.at_level("WARNING", logger="papis"):
        runner = PapisRunner()
        runner.invoke(
            cli,
            ["--all", "--batch", "url:https://youtu.be/dQw4w9WgXcQ"])

        warning, = caplog.records
        assert warning.levelname == "WARNING"
        assert warning.message == "No documents retrieved"


def test_duplicate_new_names(tmp_library: TemporaryLibrary,
                             caplog: LogCaptureFixture) -> None:
    from papis.commands.rename import cli
    from papis.testing import PapisRunner

    runner = PapisRunner()
    doc_count = len(papis.database.get().get_all_documents())

    with caplog.at_level("WARNING", logger="papis"):
        runner.invoke(
            cli,
            ["--all", "--folder-name", "same-name", "--batch"])

        # First document will rename, but all others should raise a warning
        assert len(caplog.records) == doc_count - 1
        assert all(
            os.path.basename(record.args[0]) == "same-name"
            for record in caplog.records
            )
