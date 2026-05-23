from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

import papis.config
import papis.database

if TYPE_CHECKING:
    from papis.testing import TemporaryLibrary


@pytest.mark.library_setup(settings={"database-backend": "sqlite"})
def test_schema_fields_extend_rebuilds_database(tmp_library: TemporaryLibrary) -> None:

    db = papis.database.get()
    cache_path = db.get_cache_path()
    assert os.path.exists(cache_path)

    from papis.database.sqlite import _get_sqlite_fields  # noqa: PLC2701

    initial_fields = _get_sqlite_fields(cache_path)
    assert "volume" not in initial_fields

    papis.config.set("sqlite-schema-fields-extend", ["volume"])
    db.initialize()

    rebuilt_fields = _get_sqlite_fields(cache_path)
    assert "volume" in rebuilt_fields


@pytest.mark.library_setup(settings={"database-backend": "sqlite"})
def test_database_all_query(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()
    assert db.get_backend_name() == "sqlite"

    docs = db.query(db.get_all_query_string())
    assert len(docs) > 0


@pytest.mark.library_setup(settings={"database-backend": "sqlite"})
def test_cache_path(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()
    assert os.path.exists(db.get_cache_path())

    db.clear()
    assert not os.path.exists(db.get_cache_path())


@pytest.mark.library_setup(settings={"database-backend": "sqlite"})
def test_query_by_schema_field(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()

    docs = db.query("author:Krishnamurti")
    assert len(docs) == 1
    assert docs[0]["author"] == "J. Krishnamurti"

    docs = db.query('title:"open society"')
    assert len(docs) == 1
    assert docs[0]["author"] == "K. Popper"

    docs = db.query('doi:"10.1112/plms/s2-42.1.230"')
    assert len(docs) == 1
    assert docs[0]["author"] == "Turing, A. M."

    docs = db.query("journal:London")
    assert len(docs) == 1
    assert docs[0]["author"] == "Turing, A. M."

    docs = db.query("ref:scott2008that")
    assert len(docs) == 1
    assert "Scott" in docs[0]["author"]

    docs = db.query("type:incollection")
    assert len(docs) == 2
    authors = {d["author"] for d in docs}
    assert "Scott, Michael" in authors
    assert "Schrute, Dwight K." in authors

    docs = db.query("year:2019")
    assert len(docs) == 2
    for doc in docs:
        assert doc["author"] == "test_author"


@pytest.mark.library_setup(settings={"database-backend": "sqlite"})
def test_query_by_non_schema_field(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()

    docs = db.query("volume:I")
    assert docs == []

    docs = db.query("publisher:Scranton")
    assert docs == []


@pytest.mark.library_setup(settings={"database-backend": "sqlite"})
def test_query_non_schema_field_with_extend(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()

    docs = db.query("volume:I")
    assert docs == []

    papis.config.set("sqlite-schema-fields-extend", ["volume"])
    db.initialize()

    docs = db.query("volume:I")
    assert len(docs) == 1
    assert docs[0]["author"] == "K. Popper"


@pytest.mark.library_setup(settings={"database-backend": "sqlite"})
def test_query_token_search(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()

    docs = db.query("Krishnamurti")
    assert len(docs) == 1
    assert docs[0]["author"] == "J. Krishnamurti"

    docs = db.query('"open society"')
    assert len(docs) == 1
    assert docs[0]["author"] == "K. Popper"

    # NOTE: non-prefixed substrings do not match
    docs = db.query("Krish")
    assert len(docs) == 0


@pytest.mark.library_setup(settings={"database-backend": "sqlite"})
def test_query_combined_fields(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()

    docs = db.query("author:Popper title:society")
    assert len(docs) == 1
    assert docs[0]["author"] == "K. Popper"

    docs = db.query("author:Scott AND type:incollection")
    assert len(docs) == 1
    assert "Scott" in docs[0]["author"]

    docs = db.query("author:Krishnamurti OR author:Turing")
    assert len(docs) == 2
    authors = {d["author"] for d in docs}
    assert "J. Krishnamurti" in authors
    assert "Turing, A. M." in authors

    docs_with_author = db.query("test_author")
    assert len(docs_with_author) == 2

    docs = db.query("test_author NOT title:wRkdff")
    assert len(docs) == 1
    assert "ZD9QRz" in docs[0]["title"]


@pytest.mark.library_setup(settings={"database-backend": "sqlite"})
def test_query_prefix(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()

    docs = db.query("Turi*")
    assert len(docs) == 1
    assert docs[0]["author"] == "Turing, A. M."

    docs = db.query("author:Scott*")
    assert len(docs) == 1
    assert "Scott" in docs[0]["author"]


@pytest.mark.library_setup(settings={"database-backend": "sqlite"})
def test_query_dict(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()

    docs = db.query_dict({"author": "Turing"})
    assert len(docs) == 1
    assert docs[0]["author"] == "Turing, A. M."

    docs = db.query_dict({"author": "test_author", "year": "2019"})
    assert len(docs) == 2
    for doc in docs:
        assert doc["author"] == "test_author"

    docs = db.query_dict({"author": "nonexistent_xyz", "year": "2099"})
    assert docs == []


@pytest.mark.library_setup(settings={"database-backend": "sqlite"})
def test_query_invalid_syntax_returns_empty(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()

    docs = db.query("{{{{invalid")
    assert docs == []

    docs = db.query("nonexistent_author_xyz_12345")
    assert docs == []
