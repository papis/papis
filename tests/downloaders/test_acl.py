import os

import pytest

import papis.downloaders
from papis.downloaders.acl import Downloader
from papis.testing import ResourceCache, TemporaryConfiguration

ACL_URLS = (
    "https://aclanthology.org/N04-1001",
    "https://aclanthology.org/2021.naacl-main.208",
)


def test_acl_match(tmp_config: TemporaryConfiguration) -> None:
    valid_urls = (
        "https://aclanthology.org",
        "https://aclanthology.org/bogus/link/10.1007",
        *ACL_URLS)

    invalid_urls = (
        "https://aclanthology.co.uk/article/123",
        "https://abs.org/article/123",
    )

    for url in valid_urls:
        assert isinstance(Downloader.match(url), Downloader)

    for url in invalid_urls:
        assert Downloader.match(url) is None


@pytest.mark.parametrize("url", ACL_URLS)
def test_acl_fetch(
    tmp_config: TemporaryConfiguration,
    resource_cache: ResourceCache,
    monkeypatch: pytest.MonkeyPatch,
    url: str,
) -> None:
    cls_ = papis.downloaders.get_downloader_by_name("acl")
    assert cls_ is Downloader

    down = cls_.match(url)
    assert down is not None

    uid = os.path.basename(url)
    infile = f"ACL_{uid}.html"
    outfile = f"ACL_{uid}_Out.json"

    monkeypatch.setattr(
        down, "_get_body", lambda: resource_cache.get_remote_resource(infile, url)
    )
    monkeypatch.setattr(down, "download_document", lambda: None)

    # NOTE: bibtex add some extra fields, so we just disable it for the test
    monkeypatch.setattr(down, "download_bibtex", lambda: None)

    down.fetch()
    extracted_data = down.ctx.data
    expected_data = resource_cache.get_local_resource(outfile, extracted_data)

    assert extracted_data == expected_data
