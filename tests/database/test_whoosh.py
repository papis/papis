import os
import pytest

import papis.config
import papis.database

from papis.testing import TemporaryLibrary


def database_init(libname: str) -> None:
    papis.config.set("database-backend", "whoosh", section=libname)

    # ensure database exists for the library
    db = papis.database.get(libname)
    assert db is not None

    # ensure that its clean
    db.clear()
    db.initialize()


def test_database_query(tmp_library: TemporaryLibrary) -> None:
    pytest.importorskip("whoosh")

    database_init(tmp_library.libname)
    db = papis.database.get()
    assert db.get_backend_name() == "whoosh"

    docs = db.query("*")
    all_docs = db.get_all_documents()
    assert len(docs) > 0
    assert len(docs) == len(all_docs)


def test_cache_path(tmp_library: TemporaryLibrary) -> None:
    database_init(tmp_library.libname)

    db = papis.database.get()

    assert os.path.exists(db.get_cache_path())
    assert os.path.isdir(db.get_cache_path())

    db.clear()

    assert not os.path.exists(db.get_cache_path())
