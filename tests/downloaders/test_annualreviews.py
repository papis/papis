import os
import pytest

import papis.logging
import papis.downloaders
from papis.downloaders.annualreviews import Downloader

import tests.downloaders as testlib

papis.logging.setup("DEBUG")

ANNUAL_REVIEWS_URLS = (
    "https://www.annualreviews.org/doi/10.1146/annurev-conmatphys-031214-014726",
    )


def test_annual_review_match() -> None:
    valid_urls = (
        "https://www.annualreviews.org",
        "http://www.annualreviews.org",
        "https://www.annualreviews.org/some/link/false",
        ) + ANNUAL_REVIEWS_URLS

    invalid_urls = (
        "https://www.annualreviews.com",
        "https://www.yearlyreviews.com",
        )

    for url in valid_urls:
        assert isinstance(Downloader.match(url), Downloader)

    for url in invalid_urls:
        assert Downloader.match(url) is None


@testlib.with_default_config
@pytest.mark.skip(reason="annualreviews.org disallows web scrapers (cloudflare)")
@pytest.mark.parametrize("url", ANNUAL_REVIEWS_URLS)
def test_annual_review_fetch(monkeypatch, url: str) -> None:
    cls = papis.downloaders.get_downloader_by_name("annualreviews")
    assert cls is Downloader

    down = cls.match(url)
    assert down is not None

    uid = os.path.basename(url).replace("-", "_")
    infile = "AnnualReview_{}.html".format(uid)
    outfile = "AnnualReview_{}_Out.json".format(uid)

    with monkeypatch.context() as m:
        m.setattr(down, "_get_body", testlib.get_remote_resource(infile, url))
        m.setattr(down, "download_document", lambda: None)

        # NOTE: bibtex add some extra fields, so we just disable it for the test
        m.setattr(down, "download_bibtex", lambda: None)

        down.fetch()
        extracted_data = down.ctx.data
        expected_data = testlib.get_local_resource(outfile, extracted_data)

        assert extracted_data == expected_data
