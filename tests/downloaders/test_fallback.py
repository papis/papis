import pytest

import papis.logging
import papis.downloaders
from papis.downloaders.fallback import Downloader

import tests.downloaders as testlib

papis.logging.setup("DEBUG")


FALLBACK_URLS = (
    "https://peerj.com/articles/4886/",
    "https://opus4.kobv.de/opus4-trr154/frontdoor/index/index/docId/481",
    )


@testlib.with_default_config
@pytest.mark.parametrize("url", FALLBACK_URLS)
def test_fallback_fetch(monkeypatch, url: str) -> None:
    cls = papis.downloaders.get_downloader_by_name("fallback")
    assert cls is Downloader

    down = cls.match(url)
    assert down is not None

    from urllib.parse import urlparse

    result = urlparse(url)
    uid = result.netloc.split(".")[-2]
    infile = "Fallback_{}.html".format(uid)
    outfile = "Fallback_{}_Out.json".format(uid)

    with monkeypatch.context() as m:
        m.setattr(down, "_get_body", testlib.get_remote_resource(infile, url))
        m.setattr(down, "download_document", lambda: None)

        # NOTE: bibtex add some extra fields, so we just disable it for the test
        m.setattr(down, "download_bibtex", lambda: None)

        down.fetch()
        extracted_data = down.ctx.data
        expected_data = testlib.get_local_resource(outfile, extracted_data)

        assert extracted_data == expected_data
