import os
import tempfile

from _pytest.logging import LogCaptureFixture
from _pytest.monkeypatch import MonkeyPatch

import papis.database

from papis.testing import TemporaryLibrary


def test_mv_run(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.mv import run

    db = papis.database.get()
    docs = db.get_all_documents()

    doc = docs[0]
    title = doc["title"]

    folder = doc.get_main_folder()
    assert folder is not None
    folder = os.path.basename(folder)

    with tempfile.TemporaryDirectory(dir=tmp_library.tmpdir) as new_dir:
        run(doc, new_dir)

        query_doc, = db.query_dict({"title": title})
        assert query_doc.get_main_folder() == os.path.join(new_dir, folder)


def test_mv_with_cli_and_prompt(tmp_library: TemporaryLibrary,
                                caplog: LogCaptureFixture,
                                monkeypatch: MonkeyPatch) -> None:

    import prompt_toolkit
    from papis.commands.mv import cli
    from papis.testing import PapisRunner
    runner = PapisRunner()

    with monkeypatch.context() as m:
        m.setattr(prompt_toolkit, "prompt", lambda *args, **kwargs: "test")

        with caplog.at_level("INFO", logger="papis"):
            result = runner.invoke(cli, ["--all"])
            assert result.exit_code == 0

        for doc in papis.database.get().get_all_documents():
            doc_main_folder = doc.get_main_folder()
            assert doc_main_folder
            doc_path = os.path.dirname(doc_main_folder)
            assert os.path.relpath(doc_path, tmp_library.libdir) == "test"


def test_mv_with_cli_and_plain_folder_name(tmp_library: TemporaryLibrary,
                                           caplog: LogCaptureFixture) -> None:
    from papis.commands.mv import cli
    from papis.testing import PapisRunner

    runner = PapisRunner()

    with caplog.at_level("INFO", logger="papis"):
        result = runner.invoke(cli, ["--all", "--folder-name", "test"])
        assert result.exit_code == 0

    for doc in papis.database.get().get_all_documents():
        doc_main_folder = doc.get_main_folder()
        assert doc_main_folder
        doc_path = os.path.dirname(doc_main_folder)
        assert os.path.relpath(doc_path, tmp_library.libdir) == "test"


def test_mv_with_cli_and_formatted_folder_name(tmp_library: TemporaryLibrary,
                                               caplog: LogCaptureFixture) -> None:
    import re
    from papis.commands.mv import cli
    from papis.testing import PapisRunner

    runner = PapisRunner()

    with caplog.at_level("INFO", logger="papis"):
        result = runner.invoke(cli, ["--all", "--folder-name", "{doc[year]}"])
        assert result.exit_code == 0
        folder_creations = [record for record in caplog.records
                            if re.match("Creating path", record.message)]
        doc_moves = [record for record in caplog.records
                     if re.match("Moving document", record.message)]
        doc_skips = [record for record in caplog.records
                     if re.match("Skipping", record.message)]

    docs = papis.database.get().get_all_documents()

    # Check creations of a folder for each distinct year
    distinct_doc_years = list(set([doc["year"] for doc in docs if doc["year"]]))
    assert len(folder_creations) == len(distinct_doc_years)

    # Check that all documents that have a year have been moved
    assert len(doc_moves) == len([doc for doc in docs if doc["year"]])

    # Check that all documents without years have been skipped
    assert len(doc_skips) == len([doc for doc in docs if not doc["year"]])
