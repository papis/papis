import papis.downloaders
from tests.downloaders import get_resource, get_json_resource
from unittest.mock import patch
from papis.downloaders.iopscience import Downloader
import papis.bibtex


def test_1():
    # One old paper
    url = 'https://iopscience.iop.org/article/10.1088/0026-1394/12/4/002'
    down = papis.downloaders.get_downloader(url)
    assert(down.name == 'iopscience')
    with patch.object(down, '_get_body',
            lambda: get_resource('iopscience_1.html')):
        with patch.object(down, 'download_document', lambda: None):
            down.fetch()
            correct_data = get_json_resource('iopscience_1_out.json')
            assert(down.ctx.data == correct_data)
            # with open('iopscience_1_out.json', 'w+') as f:
                # import json
                # json.dump(down.ctx.data, f)


def test_2():
    # Multiple authors with affiliations
    url = 'https://iopscience.iop.org/article/10.1088/1748-605X/ab007b'
    down = papis.downloaders.get_downloader(url)
    assert(down.name == 'iopscience')
    with patch.object(down, '_get_body',
            lambda: get_resource('iopscience_2.html')):
        with patch.object(down, 'download_document', lambda: None):
            down.fetch()
            correct_data = get_json_resource('iopscience_2_out.json')
            assert(down.ctx.data == correct_data)
            # with open('iopscience_2_out.json', 'w+') as f:
                # import json
                # json.dump(down.ctx.data, f)
