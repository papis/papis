import os
import pytest

import papis.logging
import papis.downloaders
from papis.downloaders.springer import Downloader

import tests.downloaders as testlib

papis.logging.setup("DEBUG")

SPRINGER_LINK_URLS = (
    "https://link.springer.com/article/10.1007/s10924-010-0192-1",
    "https://link.springer.com/article/10.1007/BF02727953",
    )


def test_springer_match() -> None:
    valid_urls = (
        "https://link.springer.com",
        "http://link.springer.com",
        "https://link.springer.com/bogus/link/10.1007",
        ) + SPRINGER_LINK_URLS
    invalid_urls = (
        "https://links.springer.com/article/123",
        "https://link.springer.co.uk/article/123",
        )

    for url in valid_urls:
        assert isinstance(Downloader.match(url), Downloader)

    for url in invalid_urls:
        assert Downloader.match(url) is None


@testlib.with_default_config
@pytest.mark.parametrize("url", SPRINGER_LINK_URLS)
def test_springer_fetch(monkeypatch, url: str) -> None:
    cls = papis.downloaders.get_downloader_by_name("springer")
    assert cls is Downloader

    down = cls.match(url)
    assert down is not None

    uid = os.path.basename(url).replace("-", "_")
    infile = "SpringerLink_{}.html".format(uid)
    outfile = "SpringerLink_{}_Out.json".format(uid)

    with monkeypatch.context() as m:
        m.setattr(down, "_get_body", testlib.get_remote_resource(infile, url))
        m.setattr(down, "download_document", lambda: None)

        # NOTE: bibtex add some extra fields, so we just disable it for the test
        m.setattr(down, "download_bibtex", lambda: None)

        down.fetch()
        extracted_data = down.ctx.data
        expected_data = testlib.get_local_resource(outfile, extracted_data)

        assert extracted_data == expected_data
