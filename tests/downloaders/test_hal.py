import os
import pytest

import papis.downloaders
from papis.downloaders.hal import Downloader

from papis.testing import TemporaryConfiguration, ResourceCache

HAL_URLS = (
    "https://hal.archives-ouvertes.fr/jpa-00235190",
    "https://hal.science/jpa-00235190",
    "https://tel.archives-ouvertes.fr/tel-02083632v1",
    "https://theses.hal.science/tel-02083632v1",
    )


def test_hal_match(tmp_config: TemporaryConfiguration) -> None:
    valid_urls = (
        "https://halshs.archives-ouvertes.fr/halshs-02285492",
        "https://shs.hal.science/halshs-02285492",
        "https://medihal.archives-ouvertes.fr/hal-03523188",
        "https://media.hal.science/hal-03523188",
        *HAL_URLS)
    invalid_urls = (
        "https://data.archives-ouvertes.fr/hal-02285492",
        "https://data.hal.science/hal-02285492",
        )

    for url in valid_urls:
        assert isinstance(Downloader.match(url), Downloader), url

    for url in invalid_urls:
        assert Downloader.match(url) is None, url


@pytest.mark.parametrize("url", HAL_URLS[1::2])
def test_hal_fetch(tmp_config: TemporaryConfiguration,
                   resource_cache: ResourceCache,
                   monkeypatch: pytest.MonkeyPatch,
                   url: str) -> None:
    cls = papis.downloaders.get_downloader_by_name("hal")
    assert cls is Downloader

    down = cls.match(url)
    assert down is not None

    from urllib.parse import urlparse
    result = urlparse(url)

    domain = result.netloc.split(".")[0].upper()
    uid = os.path.basename(result.path).replace("-", "_")
    infile = f"HAL_{domain}_{uid}.html"
    outfile = f"HAL_{domain}_{uid}_Out.json"

    monkeypatch.setattr(down, "_get_body",
                        lambda: resource_cache.get_remote_resource(infile, url))
    monkeypatch.setattr(down, "download_document", lambda: None)

    # NOTE: bibtex add some extra fields, so we just disable it for the test
    monkeypatch.setattr(down, "download_bibtex", lambda: None)

    down.fetch()
    extracted_data = down.ctx.data
    expected_data = resource_cache.get_local_resource(outfile, extracted_data)

    assert extracted_data == expected_data
