from papis.downloaders.utils import get_available_downloaders


def test_get_available_downloaders():
    downloaders = get_available_downloaders()
    assert(len(downloaders) > 0)
    for d in downloaders:
        assert(d is not None)
        assert(callable(d.match))
