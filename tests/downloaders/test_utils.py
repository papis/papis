from papis.downloaders.utils import (
    get_available_downloaders,
    get_downloader
)


def test_get_available_downloaders():
    downloaders = get_available_downloaders()
    assert(len(downloaders) > 0)
    for d in downloaders:
        assert(d is not None)
        assert(callable(d.match))


def test_get_downloader():
    down = get_downloader('https://google.com', 'get')
    assert(down is not None)
    assert(down.name == 'get')
    assert(str(down) == 'get')

    down = get_downloader('arXiv:1701.08223v2')
    assert(down is not None)
    assert(down.name == 'arxiv')
