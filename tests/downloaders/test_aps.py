import papis.downloaders
from unittest.mock import patch
from tests.downloaders import get_resource, get_json_resource
import logging
logging.basicConfig(level=logging.DEBUG)


def test_1():
    url = "https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.122.145901"
    down = papis.downloaders.get_downloader(url)
    assert down.name == "aps"
    with patch.object(down, "_get_body", lambda: get_resource("prl_1.html")):
        with patch.object(down, "download_document", lambda: None):
            down.fetch()
            correct_data = get_json_resource("prl_1_out.json")
            assert down.ctx.data == correct_data
            # with open("prl_1_out.json", "w+") as f:
            #     import json
            #     json.dump(down.ctx.data, f)
