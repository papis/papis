import os
import pytest

import papis.downloaders
from papis.downloaders.springer import Downloader

from papis.testing import TemporaryConfiguration, ResourceCache

SPRINGER_LINK_URLS = (
    "https://link.springer.com/article/10.1007/s10924-010-0192-1",
    "https://link.springer.com/article/10.1007/BF02727953",
    )


def test_springer_match(tmp_config: TemporaryConfiguration) -> None:
    valid_urls = (
        "https://link.springer.com",
        "http://link.springer.com",
        "https://link.springer.com/bogus/link/10.1007",
        *SPRINGER_LINK_URLS)
    invalid_urls = (
        "https://links.springer.com/article/123",
        "https://link.springer.co.uk/article/123",
        )

    for url in valid_urls:
        assert isinstance(Downloader.match(url), Downloader)

    for url in invalid_urls:
        assert Downloader.match(url) is None


@pytest.mark.parametrize("url", SPRINGER_LINK_URLS)
def test_springer_fetch(tmp_config: TemporaryConfiguration,
                        resource_cache: ResourceCache,
                        monkeypatch: pytest.MonkeyPatch,
                        url: str) -> None:
    cls = papis.downloaders.get_downloader_by_name("springer")
    assert cls is Downloader

    down = cls.match(url)
    assert down is not None

    uid = os.path.basename(url).replace("-", "_")
    infile = "SpringerLink_{}.html".format(uid)
    outfile = "SpringerLink_{}_Out.json".format(uid)

    monkeypatch.setattr(down, "_get_body",
                        lambda: resource_cache.get_remote_resource(infile, url))
    monkeypatch.setattr(down, "download_document", lambda: None)

    # NOTE: bibtex add some extra fields, so we just disable it for the test
    monkeypatch.setattr(down, "download_bibtex", lambda: None)

    down.fetch()
    extracted_data = down.ctx.data
    expected_data = resource_cache.get_local_resource(outfile, extracted_data)

    assert extracted_data == expected_data
