import os
import pytest
from _pytest.monkeypatch import MonkeyPatch

import papis.downloaders
from papis.downloaders.usenix import Downloader

from papis.testing import TemporaryConfiguration, ResourceCache

USENIX_LINK_URLS = (
    "https://www.usenix.org/conference/usenixsecurity22/presentation/bulekov",
    "https://www.usenix.org/conference/nsdi22/presentation/goyal",
    )


def download_bibtex(cache: ResourceCache, down: Downloader, infile: str) -> None:
    url = down.get_bibtex_url()
    data = cache.get_remote_resource(infile, url, cookies=down.cookies)
    down.bibtex_data = data.decode()


def test_usenix_match() -> None:
    valid_urls = (
        "https://usenix.org/conference",
        "http://usenix.org/conference",
        "https://usenix.org/bogus22/link/author",
        *USENIX_LINK_URLS)
    invalid_urls = (
        "https://usewin.org/article/123",
        "https://usenix.com/article/123",
        )

    for url in valid_urls:
        assert isinstance(Downloader.match(url), Downloader)

    for url in invalid_urls:
        assert Downloader.match(url) is None


@pytest.mark.parametrize("url", USENIX_LINK_URLS)
def test_usenix_fetch(tmp_config: TemporaryConfiguration,
                      resource_cache: ResourceCache,
                      monkeypatch: MonkeyPatch,
                      url: str) -> None:
    cls = papis.downloaders.get_downloader_by_name("usenix")
    assert cls is Downloader

    down = cls.match(url)
    assert down is not None

    uid = os.path.basename(url)
    infile = f"USENIX_{uid}.bib"
    outfile = f"USENIX_{uid}_Out.json"

    monkeypatch.setattr(down, "download_document", lambda: None)
    monkeypatch.setattr(down, "download_bibtex",
                        lambda: download_bibtex(resource_cache, down, infile))

    down.fetch()
    extracted_data = down.ctx.data
    expected_data = resource_cache.get_local_resource(outfile, extracted_data)

    assert extracted_data == expected_data
