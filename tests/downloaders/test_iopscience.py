import os
import pytest

import papis.downloaders
from papis.downloaders.iopscience import Downloader

from tests.testlib import TemporaryConfiguration, ResourceCache

IOPSCIENCE_URLS = (
    "https://iopscience.iop.org/article/10.1088/0026-1394/12/4/002",
    "https://iopscience.iop.org/article/10.1088/1748-605X/ab007b"
    )


@pytest.mark.resource_setup(cachedir="downloaders/resources")
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
    infile = "IOPScience_{}.html".format(uid)
    outfile = "IOPScience_{}_Out.json".format(uid)

    monkeypatch.setattr(down, "_get_body",
                        lambda: resource_cache.get_remote_resource(infile, url))
    monkeypatch.setattr(down, "download_document", lambda: None)

    # NOTE: bibtex add some extra fields, so we just disable it for the test
    monkeypatch.setattr(down, "download_bibtex", lambda: None)

    down.fetch()
    extracted_data = down.ctx.data
    expected_data = resource_cache.get_local_resource(outfile, extracted_data)

    assert extracted_data == expected_data
