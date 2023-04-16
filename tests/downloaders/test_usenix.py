import os
import pytest

import papis.logging
import papis.downloaders
from papis.downloaders.usenix import Downloader

import tests.downloaders as testlib

papis.logging.setup("DEBUG")

USENIX_LINK_URLS = (
    "https://www.usenix.org/conference/usenixsecurity22/presentation/bulekov",
    "https://www.usenix.org/conference/nsdi22/presentation/goyal",
    )


def download_bibtex(down: Downloader, infile: str) -> None:
    url = down.get_bibtex_url()
    data = testlib.get_remote_resource(infile, url, cookies=down.cookies)()
    down.bibtex_data = data.decode()


def test_usenix_match() -> None:
    valid_urls = (
        "https://usenix.org/conference",
        "http://usenix.org/conference",
        "https://usenix.org/bogus22/link/author",
        ) + USENIX_LINK_URLS
    invalid_urls = (
        "https://usewin.org/article/123",
        "https://usenix.com/article/123",
        )

    for url in valid_urls:
        assert isinstance(Downloader.match(url), Downloader)

    for url in invalid_urls:
        assert Downloader.match(url) is None


@testlib.with_default_config
@pytest.mark.parametrize("url", USENIX_LINK_URLS)
def test_usenix_fetch(monkeypatch, url: str) -> None:
    cls = papis.downloaders.get_downloader_by_name("usenix")
    assert cls is Downloader

    down = cls.match(url)
    assert down is not None

    uid = os.path.basename(url)
    infile = "USENIX_{}.bib".format(uid)
    outfile = "USENIX_{}_Out.json".format(uid)

    with monkeypatch.context() as m:
        m.setattr(down, "download_document", lambda: None)
        m.setattr(down, "download_bibtex", lambda: download_bibtex(down, infile))

        down.fetch()
        extracted_data = down.ctx.data
        expected_data = testlib.get_local_resource(outfile, extracted_data)

        assert extracted_data == expected_data
