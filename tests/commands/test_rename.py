import os

from _pytest.monkeypatch import MonkeyPatch

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
    import re

    from papis.commands.rename import cli
    from papis.testing import PapisRunner

    def dumb_confirm(prompt, *_) -> bool:
        print(prompt)
        return True

    runner = PapisRunner()
    first_doc_id = papis.database.get().get_all_documents()[0]["papis_id"]
    query = f"papis_id:{first_doc_id}"
    papis.config.set("add-folder-name", "{doc[papis_id]}")

    new_name_re = re.compile(r"Rename .* into (.*)\?")

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "confirm", dumb_confirm)

        # Check that the document will be renamed according to the default pattern
        result = runner.invoke(cli, [query])
        new_name = new_name_re.match(result.output).group(1)
        assert new_name == first_doc_id

        # Check that we can override the default pattern
        result = runner.invoke(cli, ["--folder-name", "magicstring42", query])
        new_name = new_name_re.match(result.output).group(1)
        assert new_name == "magicstring42"


def test_rename_batch(tmp_library: TemporaryLibrary, caplog) -> None:
    import logging

    from papis.commands.rename import cli
    from papis.testing import PapisRunner

    runner = PapisRunner()

    docs = papis.database.get().get_all_documents()
    magic_string = "magic-string42"
    papis.config.set("add-folder-name", magic_string + "-{doc[papis_id]}")
    with caplog.at_level(logging.INFO):
        runner.invoke(cli, ["--all", "--batch"])
        assert len(caplog.records) == len(docs)
        for record in caplog.records:
            assert magic_string in record.message


def test_rename_no_matching_documents(tmp_library: TemporaryLibrary, caplog) -> None:
    import logging

    from papis.commands.rename import cli
    from papis.testing import PapisRunner

    runner = PapisRunner()
    args = ["--all", "--folder-name", "--batch", "url:https://youtu.be/dQw4w9WgXcQ"]
    with caplog.at_level(logging.INFO):
        runner.invoke(cli, args)

        warnings = [r for r in caplog.records if r.levelno == logging.WARN]
        assert len(warnings) == 1


def test_duplicate_new_names(tmp_library: TemporaryLibrary, caplog) -> None:
    import logging

    from papis.commands.rename import cli
    from papis.testing import PapisRunner

    docs = papis.database.get().get_all_documents()
    runner = PapisRunner()
    with caplog.at_level(logging.WARN):
        runner.invoke(cli, ["--all", "--folder-name", "same_name", "--batch"])
        warnings = [r for r in caplog.records if r.levelno == logging.WARN]
        # First document will rename, but all others should raise a warning
        assert len(warnings) == len(docs) - 1
