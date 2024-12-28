import os
import pytest

import papis.downloaders
from papis.downloaders.sciencedirect import Downloader

from papis.testing import TemporaryConfiguration, ResourceCache

SCIENCE_DIRECT_URLS = (
    "https://www.sciencedirect.com/science/article/abs/pii/S0009261497040141",
    "https://www.sciencedirect.com/science/article/abs/pii/S2210271X18305656",
    "https://www.sciencedirect.com/science/article/pii/S146290112300117X",
    )


def test_sciencedirect_match(tmp_config: TemporaryConfiguration) -> None:
    valid_urls = (
        "https://www.sciencedirect.com",
        "http://www.sciencedirect.com/science/article/pii/S0009261497040141",
        *SCIENCE_DIRECT_URLS)
    invalid_urls = {
        "https://www.scienceindirect.com",
        "http://www.sciencedirect.co.uk/science/article/pii/S0009261497040141",
        }

    for url in valid_urls:
        assert isinstance(Downloader.match(url), Downloader)

    for url in invalid_urls:
        assert Downloader.match(url) is None


@pytest.mark.skip(reason="sciencedirect.com disallows web scraping")
@pytest.mark.parametrize("url", SCIENCE_DIRECT_URLS)
def test_sciencedirect_fetch(tmp_config: TemporaryConfiguration,
                             resource_cache: ResourceCache,
                             monkeypatch: pytest.MonkeyPatch,
                             url: str) -> None:
    cls = papis.downloaders.get_downloader_by_name("sciencedirect")
    assert cls is Downloader

    down = cls.match(url)
    assert down is not None

    uid = os.path.basename(url)
    infile = "ScienceDirect_{}.html".format(uid)
    outfile = "ScienceDirect_{}_Out.json".format(uid)

    monkeypatch.setattr(down, "_get_body",
                        lambda: resource_cache.get_remote_resource(infile, url))
    monkeypatch.setattr(down, "download_document", lambda: None)

    down.fetch()
    extracted_data = down.ctx.data
    expected_data = resource_cache.get_local_resource(outfile, extracted_data)

    assert extracted_data == expected_data
