import pytest

from papis.testing import TemporaryConfiguration
from papis.downloaders.thesesfr import Downloader


def test_match(tmp_config: TemporaryConfiguration):
    valid_urls = [
        "https://www.theses.fr/2014TOU30305",
        "2014TOU30305",  # spell: disable
        "https://www.theses.fr/2014TOU30305.bib/?asdf=2",
    ]
    invalid_urls = ["http://google.com", "2014TOU", "ASDF"]  # spell: disable
    for url in valid_urls:
        assert isinstance(Downloader.match(url), Downloader)

    for url in invalid_urls:
        assert Downloader.match(url) is None


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("https://www.theses.fr/2014TOU30305", "2014TOU30305"),  # spell: disable
        ("https://www.theses.fr/2014TOU30305.bib/?asdf=2", "2014TOU30305"),  # spell: disable
        ("2014TOU30305", "2014TOU30305"),  # spell: disable
        ("2014TOU", None),  # spell: disable
    ],
)
def test_get_identifier(query: str, expected: str, tmp_config: TemporaryConfiguration):
    d = Downloader(query)
    actual = d.get_identifier()
    assert actual == expected


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        (
            "https://theses.fr/2019REIMS014",
            "https://theses.fr/api/v1/document/2019REIMS014",
        )
    ],
)
def test_get_document_url(query: str, expected: str):
    d = Downloader(query)
    actual = d.get_document_url()
    assert actual == expected


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        (
            "https://www.theses.fr/2014TOU30305",
            "https://www.theses.fr/2014TOU30305.bib",
        ),
    ],
)
def test_get_bibtex_url(query: str, expected: str, tmp_config: TemporaryConfiguration):
    d = Downloader(query)
    actual = d.get_bibtex_url()
    assert actual == expected
