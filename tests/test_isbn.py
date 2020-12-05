import papis.isbn

def test_get_data():
    mattuck = papis.isbn.get_data(query='Mattuck feynan diagrams')
    assert(mattuck)
    assert(isinstance(mattuck, list))
    assert(isinstance(mattuck[0], dict))
    assert(mattuck[0]['isbn-13'] == '9780486670478')


def test_importer_match():
    assert(papis.isbn.Importer.match('9780486670478'))
    assert(papis.isbn.Importer.match('this-is-not-an-isbn') is None)

    # NOTE: ISBN for Wesseling - An Introduction to Multigrid Methods
    importer = papis.isbn.Importer.match('9781930217089')
    assert(importer)
    assert(importer.uri == '9781930217089')
