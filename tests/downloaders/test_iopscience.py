from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from papis.downloaders import get_downloader_by_name
from papis.downloaders.iopscience import IOPscienceDownloader

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

IOPSCIENCE_URLS = (
    "https://iopscience.iop.org/article/10.1088/0026-1394/12/4/002",
    "https://iopscience.iop.org/article/10.1088/1748-605X/ab007b"
    )


def test_iopscience_match(tmp_config: TemporaryConfiguration) -> None:
    """URLs pointing at IOPscience are matched, others rejected."""
    valid_urls = (
        "https://iopscience.iop.org",
        "https://iopscience.iop.org/article/10.1088/0026-1394/12/4/002/pdf",
        *IOPSCIENCE_URLS)
    invalid_urls = (
        "https://iop.org/article/123",
        "https://iopscience.iop.co.uk/article/123",
        )

    for url in valid_urls:
        assert isinstance(IOPscienceDownloader.match(url), IOPscienceDownloader)

    for url in invalid_urls:
        assert IOPscienceDownloader.match(url) is None


@pytest.mark.parametrize("url", IOPSCIENCE_URLS)
def test_iopscience_fetch(tmp_config: TemporaryConfiguration,
                           resource_cache: ResourceCache,
                           monkeypatch: pytest.MonkeyPatch,
                           url: str) -> None:
    """Fetch and parse metadata from an IOPscience URL."""
    cls = get_downloader_by_name("iopscience")
    assert cls is IOPscienceDownloader

    down = cls.match(url)
    assert down is not None

    uid = os.path.basename(url)
    infile = f"IOPScience_{uid}.html"
    outfile = f"IOPScience_{uid}_Out.json"

    monkeypatch.setattr(down, "_get_body",
                        lambda: resource_cache.get_remote_resource(infile, url))
    monkeypatch.setattr(down, "download_document", lambda: None)

    # NOTE: bibtex adds some extra fields, so we just disable it for the test
    monkeypatch.setattr(down, "download_bibtex", lambda: None)

    down.fetch()
    extracted_data = down.ctx.data
    expected_data = resource_cache.get_local_resource(outfile, extracted_data)

    assert extracted_data == expected_data
