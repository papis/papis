import os

import pytest

import papis.downloaders
from papis.downloaders.acs import Downloader
from tests.testlib import ResourceCache, TemporaryConfiguration

ACL_URLS = (
    "https://aclanthology.org/N04-1001",
    "https://aclanthology.org/2021.naacl-main.208/",
)

def test_acl_match(tmp_config: TemporaryConfiguration) -> None:


@pytest.mark.skip(reason="acs.org disallows web scrapers (cloudflare)")
@pytest.mark.resource_setup(cachedir="downloaders/resources")
@pytest.mark.parametrize("url", ACS_URLS)
def test_acl_fetch(
    tmp_config: TemporaryConfiguration,
    resource_cache: ResourceCache,
    monkeypatch: pytest.MonkeyPatch,
    url: str,
) -> None:
