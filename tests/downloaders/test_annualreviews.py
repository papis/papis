import os
import pytest

import papis.downloaders
from papis.downloaders.annualreviews import Downloader

from papis.testing import TemporaryConfiguration, ResourceCache

ANNUAL_REVIEWS_URLS = (
    "https://www.annualreviews.org/doi/10.1146/annurev-conmatphys-031214-014726",
    )


def test_annual_review_match(tmp_config: TemporaryConfiguration) -> None:
    valid_urls = (
        "https://www.annualreviews.org",
        "http://www.annualreviews.org",
        "https://www.annualreviews.org/some/link/false",
        *ANNUAL_REVIEWS_URLS)

    invalid_urls = (
        "https://www.annualreviews.com",
        "https://www.yearlyreviews.com",
        )

    for url in valid_urls:
        assert isinstance(Downloader.match(url), Downloader)

    for url in invalid_urls:
        assert Downloader.match(url) is None


@pytest.mark.skip(reason="annualreviews.org disallows web scrapers (cloudflare)")
@pytest.mark.parametrize("url", ANNUAL_REVIEWS_URLS)
def test_annual_review_fetch(tmp_config: TemporaryConfiguration,
                             resource_cache: ResourceCache,
                             monkeypatch: pytest.MonkeyPatch,
                             url: str) -> None:
    cls = papis.downloaders.get_downloader_by_name("annualreviews")
    assert cls is Downloader

    down = cls.match(url)
    assert down is not None

    uid = os.path.basename(url).replace("-", "_")
    infile = "AnnualReview_{}.html".format(uid)
    outfile = "AnnualReview_{}_Out.json".format(uid)

    monkeypatch.setattr(down, "_get_body",
                        lambda: resource_cache.get_remote_resource(infile, url))
    monkeypatch.setattr(down, "download_document", lambda: None)

    # NOTE: bibtex add some extra fields, so we just disable it for the test
    monkeypatch.setattr(down, "download_bibtex", lambda: None)

    down.fetch()
    extracted_data = down.ctx.data
    expected_data = resource_cache.get_local_resource(outfile, extracted_data)

    assert extracted_data == expected_data
