import os
import pytest

import papis.downloaders
from papis.downloaders.tandfonline import Downloader

from papis.testing import TemporaryConfiguration, ResourceCache

TANDFONLINE_URLS = (
    "https://www.tandfonline.com/doi/full/10.1080/00268976.2013.788745",
    "https://www.tandfonline.com/doi/full/10.1080/23311932.2015.1117749"
    )


def test_tandfonline_match(tmp_config: TemporaryConfiguration) -> None:
    valid_urls = (
        "https://tandfonline.com",
        "http://tandfonline.com",
        "https://tandfonline.com/bogus/link/10.1007",
        *TANDFONLINE_URLS)
    invalid_urls = (
        "https://torfonline.com/article/123",
        "https://tandfonline.co.uk/article/123",
        )

    for url in valid_urls:
        assert isinstance(Downloader.match(url), Downloader)

    for url in invalid_urls:
        assert Downloader.match(url) is None


@pytest.mark.skip(reason="tandfonline.com seems to require javascript")
@pytest.mark.parametrize("url", TANDFONLINE_URLS)
def test_tandfonline_fetch(tmp_config: TemporaryConfiguration,
                           resource_cache: ResourceCache,
                           monkeypatch: pytest.MonkeyPatch,
                           url: str) -> None:
    cls = papis.downloaders.get_downloader_by_name("tandfonline")
    assert cls is Downloader

    down = cls.match(url)
    assert down is not None

    uid = os.path.basename(url)
    infile = "TFOnline_{}.html".format(uid)
    outfile = "TFOnline_{}_Out.json".format(uid)

    monkeypatch.setattr(down, "_get_body",
                        lambda: resource_cache.get_remote_resource(infile, url))
    monkeypatch.setattr(down, "download_document", lambda: None)

    # NOTE: bibtex add some extra fields, so we just disable it for the test
    monkeypatch.setattr(down, "download_bibtex", lambda: None)

    down.fetch()
    extracted_data = down.ctx.data
    expected_data = resource_cache.get_local_resource(outfile, extracted_data)

    assert extracted_data == expected_data
