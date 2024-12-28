import os
import pytest

import papis.downloaders
from papis.downloaders.citeseerx import Downloader

from papis.testing import TemporaryConfiguration, ResourceCache

CITESEERX_URLS = (
    "https://citeseerx.ist.psu.edu/doc_view/pid/497490d0d3ab2724e58b03765055f7a134ce89d3",
    "https://citeseerx.ist.psu.edu/doc_view/pid/dd95519adf528fd234316f6d65ec1727d532ad97",
    )


def get_citeseerx_resource(
        resources: ResourceCache,
        filename: str, url: str,
        force: bool = False,
        ) -> bytes:
    pid = os.path.basename(url)
    return resources.get_remote_resource(
        filename, Downloader.API_URL,
        params={"paper_id": pid},
        headers={"token": "undefined", "referer": url})


@pytest.mark.skip(reason="citeseerx.ist.psu.edu does not seem to be working anymore")  # spell: disable
@pytest.mark.parametrize("url", CITESEERX_URLS)
def test_citeseerx_fetch(tmp_config: TemporaryConfiguration,
                         resource_cache: ResourceCache,
                         monkeypatch: pytest.MonkeyPatch,
                         url: str) -> None:
    cls = papis.downloaders.get_downloader_by_name("citeseerx")
    assert cls is Downloader

    down = cls.match(url)
    assert down is not None

    uid = os.path.basename(url)
    infile = "CiteSeerX_{}.json".format(uid)
    outfile = "CiteSeerX_{}_Out.json".format(uid)

    monkeypatch.setattr(down, "_get_raw_data",
                        lambda: get_citeseerx_resource(resource_cache, infile, url))
    monkeypatch.setattr(down, "download_document", lambda: None)

    down.fetch()
    extracted_data = down.ctx.data
    expected_data = resource_cache.get_local_resource(outfile, extracted_data)

    assert extracted_data == expected_data
