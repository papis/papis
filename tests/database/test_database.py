import papis.config
import papis.database

import pytest
from papis.testing import TemporaryLibrary

PAPIS_DB_BACKENDS = ["papis"]

try:
    import whoosh       # noqa: F401
    PAPIS_DB_BACKENDS.append("whoosh")
except ImportError:
    pass

PAPIS_DB_SETTINGS = [{"settings": {"database-backend": b}} for b in PAPIS_DB_BACKENDS]


@pytest.mark.parametrize("tmp_library", PAPIS_DB_SETTINGS, indirect=True)
def test_database_paths(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()
    assert db is not None
    assert db.get_backend_name() == papis.config.get("database-backend")
    assert db.get_lib() == papis.config.get_lib_name()
    assert db.get_dirs() == papis.config.get_lib_dirs()
    assert db.get_all_query_string() == papis.database.get_all_query_string()

    docs = db.get_all_documents()
    assert len(docs) > 0


@pytest.mark.parametrize("tmp_library", PAPIS_DB_SETTINGS, indirect=True)
def test_database_query(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()
    docs = db.get_all_documents()

    query_docs = db.query_dict({"title": docs[0]["title"]})
    assert len(query_docs) == 1
    assert query_docs[0] == docs[0]


@pytest.mark.parametrize("tmp_library", PAPIS_DB_SETTINGS, indirect=True)
def test_database_update(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()
    docs = db.get_all_documents()

    title = f"title for {__name__}::test_update"
    doc = docs[0]
    doc["title"] = title
    doc.save()
    db.update(doc)

    docs = db.query_dict({"title": "test_update"})
    assert len(docs) == 1
    assert docs[0]["title"] == title


@pytest.mark.parametrize("tmp_library", PAPIS_DB_SETTINGS, indirect=True)
def test_database_delete(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()

    docs = db.get_all_documents()
    ndocs = len(docs)
    db.delete(docs[0])

    ndocs_after_delete = len(db.get_all_documents())
    assert ndocs == ndocs_after_delete + 1


@pytest.mark.parametrize("tmp_library", PAPIS_DB_SETTINGS, indirect=True)
def test_database_add(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()
    docs = db.get_all_documents()
    ndocs = len(docs)

    from papis.document import from_data
    doc = from_data({
        "author": "A. Litt and C. Eliasmith and F. W. Kroon and S. Weinstein",
        "title": "Is the Brain a Quantum Computer?",
        "journal": "Cognitive Science",
        })

    import tempfile
    with tempfile.TemporaryDirectory(dir=tmp_library.tmpdir) as tmp:
        doc.set_folder(tmp)
        doc.save()
        db.add(doc)

        ndocs_after_add = len(db.get_all_documents())
        assert ndocs == ndocs_after_add - 1
