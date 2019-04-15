import papis.downloaders
from papis.downloaders.springer import Downloader
from unittest.mock import patch
from tests.downloaders import get_resource, get_json_resource
import logging
logging.basicConfig(level=logging.DEBUG)


def test_1():
    url = 'https://link.springer.com/article/10.1007/s10924-010-0192-1#citeas'
    down = papis.downloaders.get_downloader(url)
    assert(down.name == 'springer')
    with patch.object(down, '_get_body',
            lambda: get_resource('springer_1.html')):
        down.fetch()
        correct_data = get_json_resource('springer_1_out.json')
        assert(down.ctx.data == correct_data)
        # with open('springer_1_out.json', 'w+') as f:
            # import json
            # json.dump(down.ctx.data, f)

def test_2():
    url = 'https://link.springer.com/article/10.1007%2FBF02727953'
    down = papis.downloaders.get_downloader(url)
    assert(down.name == 'springer')
    with patch.object(down, '_get_body',
            lambda: get_resource('springer_2.html')):
        down.fetch()
        correct_data = get_json_resource('springer_2_out.json')
        assert(down.ctx.data == correct_data)
        # with open('springer_2_out.json', 'w+') as f:
            # import json
            # json.dump(down.ctx.data, f)
