import papis.downloaders
from papis.downloaders.tandfonline import Downloader
from unittest.mock import patch
from tests.downloaders import get_resource, get_json_resource
import logging
logging.basicConfig(level=logging.DEBUG)


def test_match():
    assert(Downloader.match(
        'https://www.tandfonline.com/science/article/pii/S0009261497040141'
    ).name == 'tandfonline')
    assert(Downloader.match(
        'https://www.tandfonline.com/science/article/pii/S2210271X18305656'
    ).name == 'tandfonline')


def test_1():
    url = 'https://www.tandfonline.com/doi/full/10.1080/00268976.2013.788745'
    down = papis.downloaders.get_downloader(url)
    assert(down.name == 'tandfonline')
    with patch.object(down, '_get_body',
            lambda: get_resource('tandfonline_1.html')):
        down.fetch()
        correct_data = get_json_resource('tandfonline_1_out.json')
        assert(down.ctx.data == correct_data)
        # with open('tandfonline_1_out.json', 'w+') as f:
            # import json
            # json.dump(down.ctx.data, f)

def test_2():
    url = 'https://www.tandfonline.com/doi/full/20.2080/00268976.2023.788745'
    down = papis.downloaders.get_downloader(url)
    assert(down.name == 'tandfonline')
    with patch.object(down, '_get_body',
            lambda: get_resource('tandfonline_2.html')):
        down.fetch()
        correct_data = get_json_resource('tandfonline_2_out.json')
        assert(down.ctx.data == correct_data)
        # with open('tandfonline_2_out.json', 'w+') as f:
            # import json
            # json.dump(down.ctx.data, f)
