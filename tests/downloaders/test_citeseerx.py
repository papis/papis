import papis.downloaders
from papis.downloaders.citeseerx import Downloader
from unittest.mock import patch
from tests.downloaders import get_resource, get_json_resource
import logging
logging.basicConfig(level=logging.DEBUG)


def test_1():
    url = 'https://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.26.2787'
    down = papis.downloaders.get_matching_downloaders(url)[0]
    assert(down.name == 'citeseerx')
    with patch.object(down,
                      '_get_body',
                      lambda: get_resource('citeseerx_1.html')):
        down.fetch_data()
        correct_data = get_json_resource('citeseerx_1_out.json')
        assert(down.ctx.data == correct_data)
