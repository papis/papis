import os
import pytest

import papis.downloaders
from papis.downloaders.iopscience import Downloader

from papis.testing import TemporaryConfiguration, ResourceCache

IOPSCIENCE_URLS = (
    "https://iopscience.iop.org/article/10.1088/0026-1394/12/4/002",
    "https://iopscience.iop.org/article/10.1088/1748-605X/ab007b"
    )


@pytest.mark.skip(reason="iopscience.iop.org blocked by radware captcha")
@pytest.mark.parametrize("url", IOPSCIENCE_URLS)
def test_iop_science_fetch(tmp_config: TemporaryConfiguration,
                           resource_cache: ResourceCache,
                           monkeypatch: pytest.MonkeyPatch,
                           url: str) -> None:
    cls = papis.downloaders.get_downloader_by_name("iopscience")
    assert cls is Downloader

    down = cls.match(url)
    assert down is not None

    uid = os.path.basename(url)
    infile = f"IOPScience_{uid}.html"
    outfile = f"IOPScience_{uid}_Out.json"

    monkeypatch.setattr(down, "_get_body",
                        lambda: resource_cache.get_remote_resource(infile, url))
    monkeypatch.setattr(down, "download_document", lambda: None)

    down.fetch()
    extracted_data = down.ctx.data
    expected_data = resource_cache.get_local_resource(outfile, extracted_data)

    assert extracted_data == expected_data
