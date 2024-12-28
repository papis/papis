import os
import pytest

import papis.downloaders
from papis.downloaders.acs import Downloader

from papis.testing import TemporaryConfiguration, ResourceCache

ACS_URLS = (
    "https://pubs.acs.org/doi/abs/10.1021/jp003647e",
    "https://pubs.acs.org/doi/abs/10.1021/acscombsci.5b00087",
    )


def test_acs_match(tmp_config: TemporaryConfiguration) -> None:
    valid_urls = (
        "https://acs.org",
        "http://acs.org",
        "https://acs.org/bogus/link/10.1007",
        *ACS_URLS)
    invalid_urls = (
        "https://acs.co.uk/article/123",
        "https://abs.org/article/123",
        )

    for url in valid_urls:
        assert isinstance(Downloader.match(url), Downloader)

    for url in invalid_urls:
        assert Downloader.match(url) is None


@pytest.mark.skip(reason="acs.org disallows web scrapers (cloudflare)")
@pytest.mark.parametrize("url", ACS_URLS)
def test_acs_fetch(tmp_config: TemporaryConfiguration,
                   resource_cache: ResourceCache,
                   monkeypatch: pytest.MonkeyPatch,
                   url: str) -> None:
    cls = papis.downloaders.get_downloader_by_name("acs")
    assert cls is Downloader

    down = cls.match(url)
    assert down is not None

    uid = os.path.basename(url)
    infile = "ACS_{}.html".format(uid)
    outfile = "ACS_{}_Out.json".format(uid)

    monkeypatch.setattr(down, "_get_body",
                        lambda: resource_cache.get_remote_resource(infile, url))
    monkeypatch.setattr(down, "download_document", lambda: None)

    # NOTE: bibtex add some extra fields, so we just disable it for the test
    monkeypatch.setattr(down, "download_bibtex", lambda: None)

    down.fetch()
    extracted_data = down.ctx.data
    expected_data = resource_cache.get_local_resource(outfile, extracted_data)

    assert extracted_data == expected_data
