from papis.isbn import *

def test_get_data():
    mattuck = get_data(query='Mattuck feynan diagrams')
    assert(mattuck)
    assert(isinstance(mattuck, list))
    assert(isinstance(mattuck[0], dict))
    assert(mattuck[0]['isbn-13'] == '9780486670478')

    result = get_data(query='Asd sdfiw 123 1Blufsh oiadsj faoisdf ')
    assert(not result)
    assert(isinstance(result, list))
