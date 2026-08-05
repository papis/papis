from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.downloaders import get_downloader_by_name
from papis.downloaders.nber import NberDownloader

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

NBER_URLS = (
    "https://www.nber.org/papers/w33843",
    "https://www.nber.org/papers/w29971",
)


def test_nber_match(tmp_config: TemporaryConfiguration) -> None:
    valid_urls = (
        "w33843",
        "https://www.nber.org/papers/w33843",
        "http://www.nber.org/papers/w29971",
        *NBER_URLS,
    )
    invalid_urls = (
        "https://www.nber.org/subscribe",
        "https://www.example.com/papers/w33843",
        "https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.122.145901",
    )

    for url in valid_urls:
        assert isinstance(NberDownloader.match(url), NberDownloader), url

    for url in invalid_urls:
        assert NberDownloader.match(url) is None, url


@pytest.mark.parametrize("url", NBER_URLS)
def test_nber_fetch(tmp_config: TemporaryConfiguration,
                    resource_cache: ResourceCache,
                    monkeypatch: pytest.MonkeyPatch,
                    url: str) -> None:
    """Fetch and parse metadata from an NBER working paper URL."""
    cls = get_downloader_by_name("nber")
    assert cls is NberDownloader

    down = cls.match(url)
    assert down is not None

    uid = down.nberid
    infile = f"NBER_{uid}.html"
    outfile = f"NBER_{uid}_Out.json"

    bib_url = down.get_bibtex_url()
    bibfile = f"NBER_{uid}.bib"

    monkeypatch.setattr(down, "_get_body",
                        lambda: resource_cache.get_remote_resource(infile, url))
    monkeypatch.setattr(down, "download_document", lambda: None)
    monkeypatch.setattr(
        down, "download_bibtex",
        lambda: setattr(
            down, "bibtex_data",
            resource_cache.get_remote_resource(bibfile, bib_url).decode(),
        ),
    )

    down.fetch()
    extracted_data = down.ctx.data
    expected_data = resource_cache.get_local_resource(outfile, extracted_data)

    assert extracted_data == expected_data
