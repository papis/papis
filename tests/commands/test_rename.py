import os
from typing import List

import pytest
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


@pytest.mark.parametrize(["regenerate", "substring"],
                         [[False, "Enter new folder name"], [True, "magic-string42"]])
def test_rename_single_entry(regenerate: List,
                             substring: str,
                             tmp_library: TemporaryLibrary,
                             monkeypatch: MonkeyPatch,
                             ) -> None:
    """
    Check that we are getting asked for a new name in normal mode or for an
    auto-generated name in --regenerate mode.
    """
    from papis.commands.rename import cli
    from papis.testing import PapisRunner

    runner = PapisRunner()

    first_doc_id = papis.database.get().get_all_documents()[0]["papis_id"]
    args = [f"papis_id:{first_doc_id}"]
    if regenerate:
        args.insert(0, "--regenerate")
        papis.config.set("add-folder-name", substring)

    def dumb_prompt(prompt, *_, default: str = "") -> str:
        print(prompt)
        return default

    def dumb_confirm(prompt, *_) -> bool:
        print(prompt)
        return True

    with monkeypatch.context() as m:
        m.setattr(papis.tui.utils, "confirm", dumb_confirm)
        m.setattr(papis.tui.utils, "prompt", dumb_prompt)
        result = runner.invoke(cli, args)
        assert substring in result.output


def test_rename_batch(tmp_library: TemporaryLibrary, caplog) -> None:
    import logging

    from papis.commands.rename import cli
    from papis.testing import PapisRunner

    runner = PapisRunner()

    docs = papis.database.get().get_all_documents()
    magic_string = "magic-string42"
    papis.config.set("add-folder-name", magic_string + "-{doc[papis_id]}")
    with caplog.at_level(logging.INFO):
        runner.invoke(cli, ["--all", "--regenerate", "--batch"])
        assert len(caplog.records) == len(docs)
        for record in caplog.records:
            assert magic_string in record.message


def test_rename_no_matching_documents(tmp_library: TemporaryLibrary, caplog) -> None:
    import logging

    from papis.commands.rename import cli
    from papis.testing import PapisRunner

    runner = PapisRunner()
    args = ["--all", "--regenerate", "--batch", "url:https://youtu.be/dQw4w9WgXcQ"]
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
    papis.config.set("add-folder-name", "foobar")
    with caplog.at_level(logging.INFO):
        runner.invoke(cli, ["--all", "--regenerate", "--batch"])
        warnings = [r for r in caplog.records if r.levelno == logging.WARN]
        # First document will rename, but all others should raise a warning
        assert len(warnings) == len(docs) - 1
