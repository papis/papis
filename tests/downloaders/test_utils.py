from papis.downloaders import (
    get_available_downloaders,
    get_matching_downloaders
)


def test_get_available_downloaders():
    downloaders = get_available_downloaders()
    assert len(downloaders) > 0
    for d in downloaders:
        assert d is not None
        assert callable(d.match)


def test_get_downloader():
    down = get_matching_downloaders("arXiv:1701.08223v2")
    assert down is not None
    assert len(down) >= 1
    assert down[0].name == "arxiv"
