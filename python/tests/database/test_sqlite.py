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
def test_database_query(tmp_library: TemporaryLibrary) -> None:
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
