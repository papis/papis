import papis.config
import papis.database

import pytest
from tests.testlib import TemporaryLibrary


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
