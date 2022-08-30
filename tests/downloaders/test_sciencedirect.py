from unittest.mock import patch

import papis.downloaders
from papis.downloaders.sciencedirect import Downloader, get_author_list

from tests.downloaders import get_resource, get_json_resource

import logging
logging.basicConfig(level=logging.DEBUG)


def test_match():
    assert Downloader.match(
        "https://www.sciencedirect.com/science/article/pii/S0009261497040141"
    )
    assert Downloader.match(
        "https://www.sciencedirect.com/science/article/pii/S2210271X18305656"
    )


def test_1():
    url = "https://www.sciencedirect.com/science/article/pii/bguss1"
    down = papis.downloaders.get_downloader(url)
    assert not down.ctx
    with patch.object(down, "_get_body", lambda: get_resource("sciencedirect_1.html")):
        with patch.object(down, "download_document", lambda: None):
            down.fetch()
            correct_data = get_json_resource("sciencedirect_1_out.json")
            assert down.ctx.data == correct_data


def test_2():
    url = "https://www.sciencedirect.com/science/article/pii/bogus"
    down = papis.downloaders.get_downloader(url)
    assert not down.ctx
    with patch.object(down, "_get_body", lambda: get_resource("sciencedirect_2.html")):
        with patch.object(down, "download_document", lambda: None):
            down.fetch()
            correct_data = get_json_resource("sciencedirect_2_out.json")
            assert down.ctx.data == correct_data


def test_get_authors():
    rawdata = get_json_resource("sciencedirect_1_authors.json")
    correct_data = get_json_resource("sciencedirect_1_authors_out.json")
    data = get_author_list(rawdata)
    assert correct_data == data
