from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from papis.downloaders import get_downloader_by_name
from papis.downloaders.aps import APSDownloader

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

APS_URLS = (
    "https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.122.145901",
    "https://journals.aps.org/prx/abstract/10.1103/PhysRevX.12.041027",
    "https://journals.aps.org/rmp/abstract/10.1103/RevModPhys.94.045004",
    )


@pytest.mark.skip(reason="aclanthology.org disallows web scrapers (cloudflare)")
@pytest.mark.parametrize("url", APS_URLS)
def test_aps_fetch(tmp_config: TemporaryConfiguration,
                   resource_cache: ResourceCache,
                   monkeypatch: pytest.MonkeyPatch,
                   url: str) -> None:
    cls = get_downloader_by_name("aps")
    assert cls is APSDownloader

    down = cls.match(url)
    assert down is not None

    uid = os.path.basename(url)
    infile = f"APS_{uid}.html"
    outfile = f"APS_{uid}_Out.json"

    monkeypatch.setattr(down, "_get_body",
                        lambda: resource_cache.get_remote_resource(infile, url))
    monkeypatch.setattr(down, "download_document", lambda: None)

    # NOTE: bibtex add some extra fields, so we just disable it for the test
    monkeypatch.setattr(down, "download_bibtex", lambda: None)

    down.fetch()
    extracted_data = down.ctx.data
    expected_data = resource_cache.get_local_resource(outfile, extracted_data)

    assert extracted_data == expected_data
