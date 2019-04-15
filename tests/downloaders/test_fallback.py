import papis.downloaders
from papis.downloaders.fallback import Downloader
from unittest.mock import patch
from tests.downloaders import get_resource, get_json_resource
import logging
logging.basicConfig(level=logging.DEBUG)


def test_1():
    url = 'asdfadfasdfasdfasdf'
    down = papis.downloaders.get_downloader(url)
    assert(down.name == 'fallback')
    with patch.object(down, '_get_body', lambda: get_resource('wiley_1.html')):
        with patch.object(down, 'download_document', lambda: None):
            down.fetch()
            correct_data = get_json_resource('fallback_1_out.json')
            assert(down.ctx.data == correct_data)
            # with open('fallback_1_out.json', 'w+') as f:
                # import json
                # json.dump(down.ctx.data, f)

def test_2():
    url = 'https://link.fallback.com/article/10.1007%2FBF02727953'
    down = papis.downloaders.get_downloader(url)
    assert(down.name == 'fallback')
    with patch.object(down, '_get_body',
            lambda: get_resource('fallback_2.html')):
        down.fetch()
        correct_data = get_json_resource('fallback_2_out.json')
        assert(down.ctx.data == correct_data)
        # with open('fallback_2_out.json', 'w+') as f:
            # import json
            # json.dump(down.ctx.data, f)
