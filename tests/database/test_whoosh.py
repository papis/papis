import os
import pytest

import papis.config
import papis.database

from papis.testing import TemporaryLibrary


@pytest.mark.library_setup(settings={"database-backend": "whoosh"})
def test_database_query(tmp_library: TemporaryLibrary) -> None:
    pytest.importorskip("whoosh")

    db = papis.database.get()
    assert db.get_backend_name() == "whoosh"

    docs = db.query("*")
    all_docs = db.get_all_documents()
    assert len(docs) > 0
    assert len(docs) == len(all_docs)


@pytest.mark.library_setup(settings={"database-backend": "whoosh"})
def test_cache_path(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()

    assert os.path.exists(db.get_cache_path())
    assert os.path.isdir(db.get_cache_path())

    db.clear()

    assert not os.path.exists(db.get_cache_path())
