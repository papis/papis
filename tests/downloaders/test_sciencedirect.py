import papis.downloaders
from papis.downloaders.sciencedirect import Downloader, get_author_list
from unittest.mock import patch
from tests.downloaders import get_resource, get_json_resource
import logging
logging.basicConfig(level=logging.DEBUG)


def test_match():
    assert(Downloader.match(
        'https://www.sciencedirect.com/science/article/pii/S0009261497040141'
    ))
    assert(Downloader.match(
        'https://www.sciencedirect.com/science/article/pii/S2210271X18305656'
    ))


def test_1():
    url = 'https://www.sciencedirect.com/science/article/pii/bguss1'
    down = papis.downloaders.get_downloader(url)
    assert(not down.ctx)
    with patch.object(down, '_get_body', lambda: get_resource('sciencedirect_1.html')):
        down.fetch()
        assert(down.ctx.data["doi"] == "10.1016/S0009-2614(97)04014-1")
        assert(down.ctx.data["abstract"])
        assert(down.ctx.data["author_list"])
        with open('sciencedirect_1_out.json', 'w+') as f:
            import json
            json.dump(down.ctx.data, f)


def test_2():
    url = 'https://www.sciencedirect.com/science/article/pii/bogus'
    down = papis.downloaders.get_downloader(url)
    assert(not down.ctx)
    with patch.object(down, '_get_body', lambda: get_resource('sciencedirect_2.html')):
        down.fetch()
        assert(down.ctx.data["doi"] == "10.1016/j.comptc.2018.10.004")
        assert(down.ctx.data["abstract"])
        assert(down.ctx.data["author_list"])
        with open('sciencedirect_2_out.json', 'w+') as f:
            import json
            json.dump(down.ctx.data, f)


def test_get_authors():
    rawdata = get_json_resource('sciencedirect_1_authors.json')
    correct_data = get_json_resource('sciencedirect_1_authors_out.json')
    data = get_author_list(rawdata)
    assert(correct_data == data)
