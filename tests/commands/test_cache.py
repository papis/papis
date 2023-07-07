import os
import sys
import pytest

from papis.commands.cache import cli
import papis.database

from tests.testlib import TemporaryLibrary, PapisRunner


def test_clear(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()

    assert not os.path.exists(db.get_cache_path())
    db.get_all_documents()
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


@pytest.mark.skipif((sys.platform == "win32") and (sys.version_info >= (3, 8)),
                    reason="For some reason update-newer does not work.")
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
    assert len(query_results) > 0

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

    # udpate
    ###################################################
    doc["cache"] = "testing"
    doc.save()

    query_results = db.query_dict({"cache": "testing"})
    assert len(query_results) == 0

    result = cli_runner.invoke(cli, ["update", "--doc-folder", folder])
    assert result.exit_code == 0

    query_results = db.query_dict({"cache": "testing"})
    assert len(query_results) == 1

    # update-newer
    ###################################################
    doc["cache"] = "end-testing"
    doc.save()

    query_results = db.query_dict({"cache": "end-testing"})
    assert len(query_results) == 0

    result = cli_runner.invoke(cli, ["update-newer", "--all"])
    assert result.exit_code == 0

    query_results = db.query_dict({"cache": "end-testing"})
    assert len(query_results) == 1
