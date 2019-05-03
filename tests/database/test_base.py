import papis.library
import papis.database.base


def test_main_database_methods():
    db = papis.database.base.Database(papis.library.Library('nonexistent', []))
    document = None
    query_string = ''

    try:
        db.initialize()
    except NotImplementedError:
        assert(True)
    else:
        assert(False)

    try:
        db.get_backend_name()
    except NotImplementedError:
        assert(True)
    else:
        assert(False)

    assert(db.get_lib() == 'nonexistent')
    assert(db.get_dirs() == [])

    try:
        db.match(document, query_string)
    except NotImplementedError:
        assert(True)
    else:
        assert(False)

    try:
        db.clear()
    except NotImplementedError:
        assert(True)
    else:
        assert(False)

    try:
        db.add(document)
    except NotImplementedError:
        assert(True)
    else:
        assert(False)

    try:
        db.update(document)
    except NotImplementedError:
        assert(True)
    else:
        assert(False)

    try:
        db.delete(document)
    except NotImplementedError:
        assert(True)
    else:
        assert(False)

    try:
        db.query(query_string)
    except NotImplementedError:
        assert(True)
    else:
        assert(False)

    try:
        db.query_dict(query_string)
    except NotImplementedError:
        assert(True)
    else:
        assert(False)

    try:
        db.get_all_documents()
    except NotImplementedError:
        assert(True)
    else:
        assert(False)

    try:
        db.get_all_query_string()
    except NotImplementedError:
        assert(True)
    else:
        assert(False)

