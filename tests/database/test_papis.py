import os

import papis.config
import papis.database
from papis.database.cache import Database

import pytest
from papis.testing import TemporaryLibrary


def database_init(libname: str) -> None:
    papis.config.set("database-backend", "papis", section=libname)

    # ensure database exists for the library
    db = papis.database.get(libname)
    assert isinstance(db, Database)

    # ensure that its clean
    db.clear()
    db.initialize()
    db.save()


def test_database_query(tmp_library: TemporaryLibrary) -> None:
    database_init(tmp_library.libname)
    db = papis.database.get()
    assert isinstance(db, Database)
    assert db.get_backend_name() == "papis"
    assert os.path.exists(db._get_cache_file_path())

    docs = db.query(".")
    all_docs = db.get_all_documents()
    assert len(docs) > 0
    assert len(docs) == len(all_docs)


def test_database_reload(tmp_library: TemporaryLibrary) -> None:
    database_init(tmp_library.libname)
    db = papis.database.get()
    assert isinstance(db, Database)

    ndocs = len(db.get_all_documents())
    db.save()
    db.documents = None

    ndocs_reload = len(db.get_all_documents())
    assert ndocs == ndocs_reload


def test_database_missing(tmp_library: TemporaryLibrary) -> None:
    database_init(tmp_library.libname)
    db = papis.database.get()
    assert isinstance(db, Database)

    docs = db.get_all_documents()
    doc = docs[0]
    db.delete(doc)

    with pytest.raises(
            Exception,
            match="document passed could not be found"):
        db._locate_document(doc)


def test_filter_documents() -> None:
    from papis.database.cache import filter_documents
    document = papis.document.from_data({"author": "einstein"})

    assert len(filter_documents([document], search="einstein")) == 1
    assert len(filter_documents([document], search="author : ein")) == 1
    assert len(filter_documents([document], search="title : ein")) != 1


def test_cache_path(tmp_library: TemporaryLibrary) -> None:
    database_init(tmp_library.libname)

    db = papis.database.get()

    assert os.path.exists(db.get_cache_path())
    assert not os.path.isdir(db.get_cache_path())
    assert os.path.isfile(db.get_cache_path())

    db.clear()

    assert not os.path.exists(db.get_cache_path())
