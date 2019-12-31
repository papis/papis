import papis.downloaders
from papis.downloaders.hal import Downloader
from unittest.mock import patch
from tests.downloaders import get_resource, get_json_resource
import logging
logging.basicConfig(level=logging.DEBUG)


def test_1():
    url = 'https://hal.archives-ouvertes.fr/jpa-00235190'
    down = papis.downloaders.get_downloader(url)
    assert(down.name == 'hal')
    with patch.object(down, '_get_body', lambda: get_resource('hal_1.html')):
        with patch.object(down, 'download_document', lambda: None):
            down.fetch()
            correct_data = get_json_resource('hal_1_out.json')
            assert(down.ctx.data == correct_data)
            # with open('hal_1_out.json', 'w+') as f:
                # import json
                # json.dump(down.ctx.data, f)
