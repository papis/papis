import os

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


def test_regenerate_name(tmp_library: TemporaryLibrary) -> None:
    from papis.commands.rename import cli
    from papis.testing import PapisRunner

    runner = PapisRunner()

    magic_string = "Test42"
    papis.config.set("add-folder-name", magic_string)
    result = runner.invoke(cli, ["--all", "--regenerate"])
    assert magic_string in result.output


def test_batch_regenerate_name(tmp_library: TemporaryLibrary,
                               caplog) -> None:
    import logging

    from papis.commands.rename import cli
    from papis.testing import PapisRunner

    runner = PapisRunner()

    docs = papis.database.get().get_all_documents()
    magic_string = "Test42"
    papis.config.set("add-folder-name", magic_string + "-{doc[papis_id]}")
    with caplog.at_level(logging.INFO):
        runner.invoke(cli, ["--all", "--regenerate", "--batch"])
        assert len(caplog.records) == len(docs)
        for record in caplog.records:
            assert magic_string in record.message
