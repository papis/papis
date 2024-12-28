import pytest

import papis.downloaders
from papis.downloaders.fallback import Downloader

from papis.testing import TemporaryConfiguration, ResourceCache

FALLBACK_URLS = (
    "https://peerj.com/articles/4886/",
    "https://opus4.kobv.de/opus4-trr154/frontdoor/index/index/docId/481",
    )


@pytest.mark.parametrize("url", FALLBACK_URLS)
def test_fallback_fetch(tmp_config: TemporaryConfiguration,
                        resource_cache: ResourceCache,
                        monkeypatch: pytest.MonkeyPatch,
                        url: str) -> None:
    cls = papis.downloaders.get_downloader_by_name("fallback")
    assert cls is Downloader

    down = cls.match(url)
    assert down is not None

    from urllib.parse import urlparse

    result = urlparse(url)
    uid = result.netloc.split(".")[-2]
    infile = f"Fallback_{uid}.html"
    outfile = f"Fallback_{uid}_Out.json"

    monkeypatch.setattr(down, "_get_body",
                        lambda: resource_cache.get_remote_resource(infile, url))
    monkeypatch.setattr(down, "download_document", lambda: None)

    # NOTE: bibtex add some extra fields, so we just disable it for the test
    monkeypatch.setattr(down, "download_bibtex", lambda: None)

    down.fetch()
    extracted_data = down.ctx.data
    expected_data = resource_cache.get_local_resource(outfile, extracted_data)

    assert extracted_data == expected_data
