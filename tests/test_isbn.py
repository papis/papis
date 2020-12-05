from papis.isbn import *

def test_get_data():
    mattuck = get_data(query='Mattuck feynan diagrams')
    assert(mattuck)
    assert(isinstance(mattuck, list))
    assert(isinstance(mattuck[0], dict))
    assert(mattuck[0]['isbn-13'] == '9780486670478')


def test_importer_match():
    assert(Importer.match('9780486670478'))
    assert(Importer.match('this-is-not-an-isbn') is None)

    # NOTE: ISBN for Wesseling - An Introduction to Multigrid Methods
    importer = Importer.match('9780471930839')
    assert(importer)
    assert(importer.uri == '9780471930839')
