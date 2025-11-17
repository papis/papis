from __future__ import annotations

import os
import json
from typing import TYPE_CHECKING
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

import pytest

from papis.downloaders import get_downloader_by_name
from papis.downloaders.lingbuzz import LingbuzzDownloader

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

LB_URLS = (
    "https://ling.auf.net/lingbuzz/006747",
    "https://lingbuzz.net/lingbuzz/008324",
)


def test_lingbuzz_match(tmp_config: TemporaryConfiguration) -> None:
    valid_urls = (
        "https://lingbuzz.net/000002",
        "https://ling.auf.net/lingbuzz/2",
        *LB_URLS)

    invalid_urls = (
        "https://lingbuzz.co.uk/000002",
        "https://arxiv.org/abs/1000.00001",
    )

    for url in valid_urls:
        assert isinstance(LingbuzzDownloader.match(url), LingbuzzDownloader)

    for url in invalid_urls:
        assert LingbuzzDownloader.match(url) is None


@pytest.mark.parametrize("url", LB_URLS)
def test_lingbuzz_fetch(
    tmp_config: TemporaryConfiguration,
    resource_cache: ResourceCache,
    monkeypatch: pytest.MonkeyPatch,
    url: str,
) -> None:
    cls_ = get_downloader_by_name("lingbuzz")
    assert cls_ is LingbuzzDownloader

    down = cls_.match(url)
    assert down is not None

    uid = os.path.basename(url)
    infile = f"Lingbuzz_{uid}.html"
    outfile = f"Lingbuzz_{uid}_Out.json"

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
