import papis.downloaders
from papis.downloaders.acs import Downloader
from tests.downloaders import get_resource, get_json_resource

import pytest
from unittest.mock import patch

import logging
logging.basicConfig(level=logging.DEBUG)


ACS_URLS = {
    'acs_1': 'https://pubs.acs.org/doi/10.1021/acscombsci.5b00087',
    'acs_2': 'https://pubs.acs.org/doi/10.1021/jp003647e',
    'acs_3': 'https://pubs.acs.org/doi/10.1021/acsphotonics.9b00250',
    'acs_4': 'https://pubs.acs.org/doi/10.1021/nl2028766'
}


def test_match():
    for k in ACS_URLS:
        assert(Downloader.match(ACS_URLS[k]))


@pytest.mark.parametrize('basename', ['acs_1', 'acs_2', 'acs_3', 'acs_4'])
def test_acs_downloader(basename):
    htmlfile = "{}.html".format(basename)
    jsonfile = "{}_out.json".format(basename)

    down = papis.downloaders.get_downloader(ACS_URLS[basename])
    assert(not down.ctx)

    # with open(htmlfile, 'w+') as f:
    #     f.write(down.session.get(url).content.decode())

    def mock_get_bibtex_url():
        raise NotImplementedError

    with patch.multiple(down,
                        _get_body=lambda: get_resource(htmlfile),
                        download_document=lambda: None,
                        get_bibtex_url=mock_get_bibtex_url):
        down.fetch()
        # with open(jsonfile, 'w+') as f:
        #     import json
        #     json.dump(down.ctx.data, f,
        #             indent=2,
        #             sort_keys=True,
        #             ensure_ascii=False)

        correct_data = get_json_resource(jsonfile)
        assert(down.ctx.data['author_list'] == correct_data['author_list'])
