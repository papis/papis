import papis.document
import papis.format
import papis.config
from tests import create_random_file, setup_test_library


def test_basic():
    setup_test_library()
    document = papis.document.from_data(
        dict(author='Fulano', title='Something'))

    assert papis.format.format('{doc[author]}{doc[title]}', document) == \
        'FulanoSomething'
    assert(papis.format.format('{doc[author]}{doc[title]}{doc[blahblah]}',
                               document) == 'FulanoSomething')

    assert(papis.format.format(
        '{doc[author]}{doc[title]}{doc[blahblah]}', dict(title='hell'))
        == 'hell')
