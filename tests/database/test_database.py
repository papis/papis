from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import papis.config
import papis.database

if TYPE_CHECKING:
    from papis.testing import TemporaryLibrary

PAPIS_DB_BACKENDS = ["papis", "sqlite"]

try:
    import whoosh  # ruff:ignore[unused-import]
    PAPIS_DB_BACKENDS.append("whoosh")
except ImportError:
    pass

PAPIS_DB_SETTINGS = [{"settings": {"database-backend": b}} for b in PAPIS_DB_BACKENDS]


@pytest.mark.parametrize("tmp_library", PAPIS_DB_SETTINGS, indirect=True)
def test_database_paths(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()

    assert db is not None
    assert db.get_backend_name() == papis.config.getstring("database-backend")
    assert db.lib.name == papis.config.get_lib_name()
    assert db.lib.path == papis.config.get_lib().path
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


@pytest.mark.parametrize("tmp_library", PAPIS_DB_SETTINGS, indirect=True)
def test_database_cache_same_library_via_different_paths(
    tmp_library: TemporaryLibrary,
) -> None:
    """:func:`papis.database.get` returns the same library instance regardless of
    whether it was resolved via :func:`~papis.config.get_lib` or
    :func:`~papis.config.get_lib_from_name`."""
    db_via_current = papis.database.get()
    lib_name = papis.config.get_lib_name()

    db_via_name = papis.database.get(library_name=lib_name)

    assert db_via_current is db_via_name


@pytest.mark.parametrize("tmp_library", PAPIS_DB_SETTINGS, indirect=True)
def test_find_by_folder(tmp_library: TemporaryLibrary) -> None:
    """``find_by_folder`` returns the correct document or ``None``."""
    db = papis.database.get()

    docs = db.get_all_documents()
    assert len(docs) > 0

    doc = docs[0]
    folder = doc.get_main_folder()
    assert folder is not None

    found = db.find_by_folder(folder)
    assert found is not None
    assert found["papis_id"] == doc["papis_id"]

    # Non-existent folder returns None
    assert db.find_by_folder("/nonexistent/path/to/doc") is None


@pytest.mark.parametrize("tmp_library", PAPIS_DB_SETTINGS, indirect=True)
def test_query_paged_sort_config_fallback(tmp_library: TemporaryLibrary) -> None:
    """Config sort-field applies queries returning all docs, but not otherwise."""
    from papis.id import ID_KEY_NAME

    db = papis.database.get()
    all_query = db.get_all_query_string()

    # baseline order of a search without any config
    docs, total = db.query_paged("Test")
    assert total >= 2
    baseline = [d[ID_KEY_NAME] for d in docs]

    # the configured sort field must not reorder search results
    papis.config.set("sort-field", "title")
    docs, total = db.query_paged("Test")
    assert total >= 2
    assert [d[ID_KEY_NAME] for d in docs] == baseline

    # but it does order non-query (browse) requests
    docs, total = db.query_paged(all_query)
    assert total >= 2
    titles = [d["title"] for d in docs]
    assert titles == sorted(titles)

    # explicit sort without explicit reverse falls back to config sort-reverse
    papis.config.set("sort-reverse", True)
    docs, total = db.query_paged(all_query, sort="title")
    assert total >= 2
    titles = [d["title"] for d in docs]
    assert titles == sorted(titles, reverse=True)

    # explicit reverse overrides the configured sort-reverse
    docs, total = db.query_paged(all_query, sort="title", reverse=False)
    assert total >= 2
    titles = [d["title"] for d in docs]
    assert titles == sorted(titles)

    # an explicit sort still wins over relevance for searches
    docs, total = db.query_paged("Test", sort="title")
    assert total >= 2
    titles = [d["title"] for d in docs]
    assert titles == sorted(titles, reverse=True)


@pytest.mark.parametrize("tmp_library", PAPIS_DB_SETTINGS, indirect=True)
def test_query_paged_paging(tmp_library: TemporaryLibrary) -> None:
    """Paged queries return consistent, disjoint pages covering the library."""
    db = papis.database.get()
    all_docs = db.get_all_documents()
    assert len(all_docs) > 1

    all_query = db.get_all_query_string()
    all_ids = {d["papis_id"] for d in all_docs}

    # the bounded path: no filters, no sort
    docs, total = db.query_paged(all_query, limit=1, offset=0)
    assert total == len(all_docs)
    assert len(docs) == 1
    assert docs[0]["papis_id"] in all_ids

    # consecutive pages are disjoint and cover the whole library
    all_pages = []
    offset = 0
    while True:
        page, total = db.query_paged(all_query, limit=2, offset=offset)
        if not page:
            break
        all_pages.extend(page)
        offset += len(page)
    assert total == len(all_docs)
    assert len(all_pages) == len(all_docs)
    assert {d["papis_id"] for d in all_pages} == all_ids

    # offset beyond the total yields an empty page with the correct total
    docs, total = db.query_paged(all_query, limit=10, offset=len(all_docs) + 100)
    assert total == len(all_docs)
    assert docs == []


@pytest.mark.parametrize("tmp_library", PAPIS_DB_SETTINGS, indirect=True)
def test_query_paged_id(tmp_library: TemporaryLibrary) -> None:
    """ID filtering: exact match, no match, empty, AND semantics with a query."""
    from papis.id import ID_KEY_NAME

    db = papis.database.get()
    all_docs = db.get_all_documents()
    assert len(all_docs) > 1

    all_query = db.get_all_query_string()

    # the all-query string matches all documents
    docs, total = db.query_paged(all_query)
    assert total == len(all_docs)
    assert len(docs) == len(all_docs)

    doc = all_docs[0]
    doc_id = str(doc[ID_KEY_NAME])

    # exact ID match
    docs, total = db.query_paged(all_query, ids=[doc_id])
    assert total == 1
    assert docs[0][ID_KEY_NAME] == doc_id

    # unknown ID matches nothing
    docs, total = db.query_paged(all_query, ids=["deadbeefdeadbeefdeadbeefdeadbeef"])
    assert total == 0
    assert docs == []

    # empty ID sequence matches nothing
    docs, total = db.query_paged(all_query, ids=[])
    assert total == 0
    assert docs == []

    # ID combined with a query string (AND semantics)
    query_docs = db.query("Krishnamurti")
    assert len(query_docs) == 1
    query_id = str(query_docs[0][ID_KEY_NAME])
    docs, total = db.query_paged("Krishnamurti", ids=[query_id])
    assert total == 1
    assert docs[0][ID_KEY_NAME] == query_id

    # ID that does not match the query yields no results
    other_id = str(all_docs[-1][ID_KEY_NAME])
    docs, total = db.query_paged("Krishnamurti", ids=[other_id])
    assert total == 0
    assert docs == []

    # multiple IDs match any of the listed IDs (OR within the list)
    docs, total = db.query_paged(all_query, ids=[doc_id, other_id])
    assert total == 2
    assert {d[ID_KEY_NAME] for d in docs} == {doc_id, other_id}

    # multiple IDs still combine with a query via AND semantics
    docs, total = db.query_paged("Krishnamurti", ids=[query_id, other_id])
    assert total == 1
    assert docs[0][ID_KEY_NAME] == query_id


@pytest.mark.parametrize("tmp_library", PAPIS_DB_SETTINGS, indirect=True)
def test_query_paged_folder_matching(tmp_library: TemporaryLibrary) -> None:
    """Folder prefix matching is exact, literal, and case-sensitive."""
    import os

    from papis.document import from_data

    db = papis.database.get()
    all_query = db.get_all_query_string()

    def _add_doc(relfolder: str) -> None:
        folder = os.path.join(tmp_library.libdir, relfolder)
        os.makedirs(folder, exist_ok=True)
        doc = from_data({"title": relfolder})
        doc.set_folder(folder)
        doc.save()
        db.add(doc)

    _add_doc("group/my_notes")
    _add_doc("group/myXnotes/sub")
    _add_doc("group/Papers/sub")
    _add_doc("group/other/sub")

    # '_' is not a wildcard: only the exact folder matches
    docs, total = db.query_paged(all_query, folder="group/my_notes")
    assert total == 1
    assert docs[0].get_main_folder() == os.path.join(
        tmp_library.libdir, "group/my_notes"
    )

    # '%' is not a wildcard
    docs, total = db.query_paged(all_query, folder="group/my%otes")
    assert total == 0
    assert docs == []

    # matching is case-sensitive
    _docs, total = db.query_paged(all_query, folder="group/papers")
    assert total == 0
    docs, total = db.query_paged(all_query, folder="group/Papers")
    assert total == 1
    assert docs[0].get_main_folder() == os.path.join(
        tmp_library.libdir, "group/Papers/sub"
    )
