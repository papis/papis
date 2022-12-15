import os
import pytest
from typing import Callable

import papis.downloaders
from papis.downloaders.citeseerx import Downloader

import logging
logging.basicConfig(level=logging.DEBUG)

CITESEERX_URLS = (
    "https://citeseerx.ist.psu.edu/doc_view/pid/497490d0d3ab2724e58b03765055f7a134ce89d3",  # noqa: E501
    "https://citeseerx.ist.psu.edu/doc_view/pid/dd95519adf528fd234316f6d65ec1727d532ad97",  # noqa: E501
    )


def get_citeseerx_resource(
        filename: str, url: str,
        force: bool = False,
        ) -> Callable[[], bytes]:
    from tests.downloaders import get_remote_resource

    pid = os.path.basename(url)
    return get_remote_resource(
        filename, Downloader.API_URL,
        params={"paper_id": pid},
        headers={"token": "undefined", "referer": url})


@pytest.mark.parametrize("url", CITESEERX_URLS)
def test_citeseerx_fetch(monkeypatch, url: str) -> None:
    cls = papis.downloaders.get_downloader_by_name("citeseerx")
    assert cls is Downloader

    down = cls.match(url)
    assert down is not None

    uid = os.path.basename(url).replace("-", "_")
    infile = "CiteSeerX_{}.json".format(uid)
    outfile = "CiteSeerX_{}_Out.json".format(uid)

    from tests.downloaders import get_local_resource

    with monkeypatch.context() as m:
        m.setattr(down, "_get_raw_data", get_citeseerx_resource(infile, url))
        m.setattr(down, "download_document", lambda: None)

        down.fetch()
        extracted_data = down.ctx.data
        expected_data = get_local_resource(outfile, extracted_data)

        assert extracted_data == expected_data
