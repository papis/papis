import os

import pytest
from papis.testing import TemporaryLibrary


@pytest.mark.library_setup(settings={"database-backend": "papis"})
def test_database_query(tmp_library: TemporaryLibrary) -> None:
    import papis.database

    db = papis.database.get()
    db.initialize()

    assert isinstance(db, papis.database.cache.Database)
    assert db.get_backend_name() == "papis"

    docs = db.query(".")
    all_docs = db.get_all_documents()
    assert len(docs) > 0
    assert len(docs) == len(all_docs)

    # NOTE: the filepath is only created once a document is queried
    assert os.path.exists(db.get_cache_path())


@pytest.mark.library_setup(settings={"database-backend": "papis"})
def test_database_reload(tmp_library: TemporaryLibrary) -> None:
    import papis.database

    db = papis.database.get()
    assert isinstance(db, papis.database.cache.Database)

    ndocs = len(db.get_all_documents())

    assert isinstance(db, papis.database.cache.Database)
    db._save_documents()
    db.documents = None

    ndocs_reload = len(db.get_all_documents())
    assert ndocs == ndocs_reload


@pytest.mark.library_setup(settings={"database-backend": "papis"})
def test_database_missing(tmp_library: TemporaryLibrary) -> None:
    import papis.database

    db = papis.database.get()
    assert isinstance(db, papis.database.cache.Database)

    docs = db.get_all_documents()
    doc = docs[0]
    db.delete(doc)

    assert isinstance(db, papis.database.cache.Database)
    with pytest.raises(
            Exception,
            match="Document could not be found"):
        db._locate_document(doc)


def test_filter_documents() -> None:
    from papis.document import from_data
    from papis.database.cache import filter_documents

    document = from_data({"author": "einstein"})

    assert len(filter_documents([document], search="einstein")) == 1
    assert len(filter_documents([document], search="author : ein")) == 1
    assert len(filter_documents([document], search="title : ein")) != 1


@pytest.mark.library_setup(settings={"database-backend": "papis"})
def test_cache_path(tmp_library: TemporaryLibrary) -> None:
    import papis.database

    db = papis.database.get()
    _ = db.get_all_documents()

    assert os.path.exists(db.get_cache_path())
    assert not os.path.isdir(db.get_cache_path())
    assert os.path.isfile(db.get_cache_path())

    db.clear()

    assert not os.path.exists(db.get_cache_path())
