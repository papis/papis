import os
import pytest

import papis.logging
import papis.downloaders
from papis.downloaders.tandfonline import Downloader

import tests
import tests.downloaders as testlib

papis.logging.setup("DEBUG")

TANDFONLINE_URLS = (
    "https://www.tandfonline.com/doi/full/10.1080/00268976.2013.788745",
    "https://www.tandfonline.com/doi/full/10.1080/23311932.2015.1117749"
    )

def test_tandfonline_match():
    valid_urls = (
        "https://tandfonline.com",
        "http://tandfonline.com",
        "https://tandfonline.com/bogus/link/10.1007",
        ) + TANDFONLINE_URLS
    invalid_urls = (
        "https://torfonline.com/article/123",
        "https://tandfonline.co.uk/article/123",
        )

    for url in valid_urls:
        assert isinstance(Downloader.match(url), Downloader)

    for url in invalid_urls:
        assert Downloader.match(url) is None


@tests.with_default_config()
@pytest.mark.parametrize("url", TANDFONLINE_URLS)
def test_tandfonline_fetch(monkeypatch, url: str) -> None:
    cls = papis.downloaders.get_downloader_by_name("tandfonline")
    assert cls is Downloader

    down = cls.match(url)
    assert down is not None

    uid = os.path.basename(url)
    infile = "TFOnline_{}.html".format(uid)
    outfile = "TFOnline_{}_Out.json".format(uid)

    with monkeypatch.context() as m:
        m.setattr(down, "_get_body", testlib.get_remote_resource(infile, url))
        m.setattr(down, "download_document", lambda: None)

        # NOTE: bibtex add some extra fields, so we just disable it for the test
        m.setattr(down, "download_bibtex", lambda: None)

        down.fetch()
        extracted_data = down.ctx.data
        expected_data = testlib.get_local_resource(outfile, extracted_data)

        assert extracted_data == expected_data
