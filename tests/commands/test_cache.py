import os
import time

from papis.commands.cache import cli
import papis.database

from papis.testing import TemporaryLibrary, PapisRunner


def test_clear(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()
    assert os.path.exists(db.get_cache_path())

    cli_runner = PapisRunner()
    result = cli_runner.invoke(cli, ["clear"])
    assert result.exit_code == 0
    assert not os.path.exists(db.get_cache_path())


def test_pwd(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()

    cli_runner = PapisRunner()
    result = cli_runner.invoke(cli, ["pwd"])
    assert db.get_cache_path() == result.output.replace("\n", "")


def test_rm_add_update(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()
    cli_runner = PapisRunner()

    docs = db.get_all_documents()
    doc = docs[0]
    title = doc["title"]
    folder = doc.get_main_folder()
    assert folder is not None

    # rm
    ###################################################
    query_results = db.query_dict({"title": title})
    assert len(query_results) == 1

    result = cli_runner.invoke(cli, ["rm", "--doc-folder", folder])
    assert result.exit_code == 0

    query_results = db.query_dict({"title": title})
    assert len(query_results) == 0

    # add
    ###################################################
    result = cli_runner.invoke(cli, ["add", "--doc-folder", folder])
    assert result.exit_code == 0

    query_results = db.query_dict({"title": title})
    assert len(query_results) == 1

    # update
    ###################################################
    # NOTE: modifying `doc` directly may modify the version in the database, so
    # this modifies the info file behind its back completely to check the update
    doc_dict = {**dict(doc), "tags": "test-update"}
    papis.yaml.data_to_yaml(doc.get_info_file(), doc_dict, allow_unicode=True)

    query_results = db.query_dict({"tags": "test-update"})
    assert len(query_results) == 0

    result = cli_runner.invoke(cli, ["update", "--doc-folder", folder])
    assert result.exit_code == 0

    query_results = db.query_dict({"tags": "test-update"})
    assert len(query_results) == 1

    # update-newer
    ###################################################
    # NOTE: `update-newer` checks mtimes, so we wait a bit so that the mtime is
    # meaningfully changed and the OS had time to update it
    time.sleep(1)

    doc_dict = {**dict(doc), "tags": "test-update-newer"}
    papis.yaml.data_to_yaml(doc.get_info_file(), doc_dict, allow_unicode=True)

    query_results = db.query_dict({"tags": "test-update-newer"})
    assert len(query_results) == 0

    result = cli_runner.invoke(cli, ["update-newer", "--all"])
    assert result.exit_code == 0

    query_results = db.query_dict({"tags": "test-update-newer"})
    assert len(query_results) == 1
