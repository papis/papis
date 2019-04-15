import papis.downloaders
from papis.downloaders.annualreviews import Downloader
from unittest.mock import patch
from tests.downloaders import get_resource, get_json_resource
import logging
logging.basicConfig(level=logging.DEBUG)


def test_match():
    assert(Downloader.match(
        'http://anualreviews.org/doi/pdf/'
        '10.1146/annurev-conmatphys-031214-014726'
    ) is False)

    assert(Downloader.match(
        'http://annualreviews.org/doi/pdf/'
        '10.1146/annurev-conmatphys-031214-014726'
    ))


def test_1():
    url = ('https://www.annualreviews.org/doi/10.1146/'
           'annurev-conmatphys-031214-014726')
    down = papis.downloaders.get_downloader(url)
    assert(down.name == 'annualreviews')
    with patch.object(down, '_get_body',
            lambda: get_resource('annualreviews_1.html')):
        with patch.object(down, 'download_document', lambda: None):
            down.fetch()
            # with open('annualreviews_1_out.json', 'w+') as f:
                # import json
                # json.dump(down.ctx.data, f)
            correct_data = get_json_resource('annualreviews_1_out.json')
            assert(down.ctx.data == correct_data)
