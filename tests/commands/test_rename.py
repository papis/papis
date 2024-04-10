import os

import papis.database
from papis.testing import TemporaryLibrary, TemporaryConfiguration


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


def test_regenerate_name(tmp_library: TemporaryLibrary,
                         tmp_config: TemporaryConfiguration,
                         ) -> None:
    from click.testing import CliRunner
    from papis.commands.rename import cli

    runner = CliRunner(mix_stderr=False)

    magic_string = "Test42"
    papis.config.set("add-folder-name", magic_string)
    result = runner.invoke(cli, ["--all", "--regenerate"])
    assert magic_string in result.output


def test_batch_regenerate_name(tmp_library: TemporaryLibrary,
                               tmp_config: TemporaryConfiguration,
                               caplog) -> None:
    import logging

    from click.testing import CliRunner
    from papis.commands.rename import cli

    runner = CliRunner(mix_stderr=False)

    docs = papis.database.get().get_all_documents()
    magic_string = "Test42"
    papis.config.set("add-folder-name", magic_string + "-{doc[papis_id]}")
    with caplog.at_level(logging.INFO):
        runner.invoke(cli, ["--all", "--regenerate", "--batch"])
        assert len(caplog.records) == len(docs)
        for record in caplog.records:
            assert magic_string in record.text
