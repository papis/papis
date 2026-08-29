from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.downloaders.thesesfr import TheseFrDownloader

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration


def test_thesesfr_match(tmp_config: TemporaryConfiguration) -> None:
    valid_urls = [
        "https://www.theses.fr/2014TOU30305",
        "2014TOU30305",  # spell: disable
        "https://www.theses.fr/2014TOU30305.bib/?asdf=2",
    ]
    invalid_urls = ["http://google.com", "2014TOU", "ASDF"]  # spell: disable
    for url in valid_urls:
        assert isinstance(TheseFrDownloader.match(url), TheseFrDownloader)

    for url in invalid_urls:
        assert TheseFrDownloader.match(url) is None


@pytest.mark.resource_setup(cachedir="resources")
def test_thesesfr_fetch(tmp_config: TemporaryConfiguration,
                        resource_cache: ResourceCache,
                        monkeypatch: pytest.MonkeyPatch,
                        ) -> None:
    """Metadata is fetched from the BibTeX endpoint."""
    url = "https://theses.fr/2014TOU30305"
    down = TheseFrDownloader.match(url)
    assert down is not None

    infile = "TheseFr_2014TOU30305.bib"
    bib_url = down.get_bibtex_url()
    assert bib_url is not None

    monkeypatch.setattr(down, "download_document", lambda: None)
    monkeypatch.setattr(
        down, "download_bibtex",
        lambda: setattr(
            down, "bibtex_data",
            resource_cache.get_remote_resource(infile, bib_url).decode(),
        ),
    )

    down.fetch()
    extracted_data = down.ctx.data
    expected_data = resource_cache.get_local_resource(
        "TheseFr_2014TOU30305_Out.json", extracted_data)

    assert extracted_data == expected_data


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("https://www.theses.fr/2014TOU30305", "2014TOU30305"),  # spell: disable
        ("https://www.theses.fr/2014TOU30305.bib/?asdf=2", "2014TOU30305"),  # spell: disable
        ("2014TOU30305", "2014TOU30305"),  # spell: disable
        ("2014TOU", None),  # spell: disable
    ],
)
def test_get_identifier(query: str, expected: str,
                        tmp_config: TemporaryConfiguration) -> None:
    d = TheseFrDownloader(query)
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
def test_get_document_url(query: str, expected: str) -> None:
    d = TheseFrDownloader(query)
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
def test_get_bibtex_url(query: str, expected: str,
                        tmp_config: TemporaryConfiguration) -> None:
    d = TheseFrDownloader(query)
    actual = d.get_bibtex_url()
    assert actual == expected
