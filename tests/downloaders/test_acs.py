import papis.downloaders
from papis.downloaders.acs import Downloader
from unittest.mock import patch
from tests.downloaders import get_resource, get_json_resource
import logging
logging.basicConfig(level=logging.DEBUG)


def test_match():
    assert(Downloader.match(
        'https://www.acs.org/science/article/pii/S0009261497040141'
    ))
    assert(Downloader.match(
        'https://www.acs.org/science/article/pii/S2210271X18305656'
    ))


def test_acs_1():
    url = 'https://pubs.acs.org/doi/10.1021/acscombsci.5b00087'
    down = papis.downloaders.get_downloader(url)
    assert(not down.ctx)
    with patch.object(down, '_get_body', lambda: get_resource('acs_1.html')):
        with patch.object(down, 'download_document', lambda: None):
            down.fetch()
            with open('acs_1_out.json', 'w+') as f:
                import json
                json.dump(down.ctx.data, f)
            correct_data = get_json_resource('acs_1_out.json')
            assert(down.ctx.data == correct_data)


def test_acs_2():
    url = 'https://pubs.acs.org/doi/10.1021/jp003647e'
    down = papis.downloaders.get_downloader(url)
    assert(not down.ctx)
    with patch.object(down, '_get_body', lambda: get_resource('acs_2.html')):
        with patch.object(down, 'download_document', lambda: None):
            down.fetch()
            with open('acs_2_out.json', 'w+') as f:
                import json
                json.dump(down.ctx.data, f)
            correct_data = get_json_resource('acs_2_out.json')
            assert(down.ctx.data == correct_data)
