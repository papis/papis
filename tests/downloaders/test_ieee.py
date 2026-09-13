from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from papis.downloaders.ieee import IEEEDownloader

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch

    from papis.testing import TemporaryConfiguration

IEEE_LINK_URLS = [
    "https://ieeexplore.ieee.org/document/10301652",
    "https://ieeexplore.ieee.org/abstract/document/10301652",
    "ieee:10301652",
]


def test_ieee_match() -> None:
    valid_urls = (
        "https://ieeexplore.ieee.org/document/10301652",
        "https://ieeexplore.ieee.org/abstract/document/10301652",
        "ieee:10301652",
        "https://ieeexplore.ieee.org/some.pdf",
    )
    invalid_urls = (
        "https://example.org/article/123",
        "https://ieeexplore.com/article/123",
    )

    for url in valid_urls:
        assert isinstance(IEEEDownloader.match(url), IEEEDownloader), url

    for url in invalid_urls:
        assert IEEEDownloader.match(url) is None, url


@pytest.mark.parametrize("url,identifier", [
    ("https://ieeexplore.ieee.org/document/10301652", "10301652"),
    ("https://ieeexplore.ieee.org/document/10301652/", "10301652"),
    ("https://ieeexplore.ieee.org/abstract/document/10301652", "10301652"),
    ("https://ieeexplore.ieee.org/abstract/document/10301652/", "10301652"),
    ("https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=10301652",
     "10301652"),
    ("ieee:10301652", "10301652"),
])
def test_get_identifier(url: str, identifier: str) -> None:
    down = IEEEDownloader(url)
    assert down.get_identifier() == identifier


def test_ieee_fetch(tmp_config: TemporaryConfiguration,
                     monkeypatch: MonkeyPatch) -> None:
    url = "https://ieeexplore.ieee.org/document/10301652"
    down = IEEEDownloader.match(url)
    assert down is not None
    assert isinstance(down, IEEEDownloader)

    bibtex = (
        "@article{10301652,\n"
        "  title = {Sample IEEE Title},\n"
        "  author = {Doe, Jane and Smith, John},\n"
        "  journal = {IEEE Transactions on Testing},\n"
        "  year = {2023},\n"
        "  doi = {10.1109/TEST.2023.10301652},\n"
        "}\n"
    )
    monkeypatch.setattr(down, "download_bibtex",
                        lambda: setattr(down, "bibtex_data", bibtex))
    monkeypatch.setattr(down, "get_data", lambda: {})

    down.fetch_data()
    data = down.ctx.data

    assert data["title"] == "Sample IEEE Title"
    assert data["year"] == "2023"
    assert data["doi"] == "10.1109/TEST.2023.10301652"


def test_ieee_bibtex_request_payload(tmp_config: TemporaryConfiguration) -> None:
    """`_get_bibtex_request` returns a POST URL + JSON body matching IEEE's
    frontend: `recordIds` as a list and `lite` as a boolean."""
    down = IEEEDownloader("https://ieeexplore.ieee.org/document/10301652")

    url, body = down._get_bibtex_request()

    assert url == "https://ieeexplore.ieee.org/rest/search/citation/format"
    assert body == {
        "recordIds": ["10301652"],
        "download-format": "download-bibtex",
        "lite": True,
    }
    # Strong type assertions: IEEE's API rejects strings.
    assert isinstance(body["recordIds"], list)
    assert isinstance(body["lite"], bool)


def test_ieee_download_bibtex_post(
        tmp_config: TemporaryConfiguration,
        monkeypatch: MonkeyPatch) -> None:
    """`download_bibtex` POSTs the JSON body and stores the cleaned response."""
    down = IEEEDownloader("https://ieeexplore.ieee.org/document/10301652")

    captured: dict[str, Any] = {}

    class _FakeResponse:
        ok = True

        def json(self):
            return {"data": "@article{10301652,<br>title={T &amp; U},}"}

    def _fake_post(url, json=None, headers=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return _FakeResponse()

    monkeypatch.setattr(down.session, "post", _fake_post)

    down.download_bibtex()

    assert captured["url"] == \
        "https://ieeexplore.ieee.org/rest/search/citation/format"
    assert captured["json"] == {
        "recordIds": ["10301652"],
        "download-format": "download-bibtex",
        "lite": True,
    }
    assert captured["headers"]["Content-Type"] == "application/json"
    assert captured["headers"]["X-Security-Request"] == "required"
    assert captured["headers"]["Referer"] == down.uri
    # JSON ``data`` extracted; ``<br>`` stripped; HTML entities unescaped.
    assert down.bibtex_data == "@article{10301652,title={T & U},}"


def test_ieee_importer_bibtex(tmp_config: TemporaryConfiguration,
                              monkeypatch: MonkeyPatch) -> None:
    """When IEEE's API serves BibTeX, the importer uses it and never falls back."""
    from papis.importer.ieee import IEEEImporter

    url = "https://ieeexplore.ieee.org/document/10301652"
    imp = IEEEImporter.match(url)
    assert isinstance(imp, IEEEImporter)

    bibtex = (
        "@article{10301652,\n"
        "  title = {Sample IEEE Title},\n"
        "  author = {Doe, Jane and Smith, John},\n"
        "  journal = {IEEE Transactions on Testing},\n"
        "  year = {2023},\n"
        "}\n"
    )
    down = imp._downloader
    monkeypatch.setattr(down, "download_bibtex",
                        lambda: setattr(down, "bibtex_data", bibtex))
    monkeypatch.setattr(down, "get_data", lambda: {})

    # Sentinel: fetch_files must NOT be called from fetch_data, and the
    # PDF/DOI fallback must NOT be invoked when BibTeX succeeds.
    def _fail_extract(self) -> str | None:
        raise AssertionError(
            "PDF fallback must not fire when BibTeX returns data")
    monkeypatch.setattr(IEEEImporter, "_extract_doi_from_pdf", _fail_extract)

    imp.fetch_data()
    assert imp.ctx.data["title"] == "Sample IEEE Title"
    assert imp.ctx.files == []


@pytest.mark.parametrize("url", IEEE_LINK_URLS)
def test_ieee_importer_pdf_doi_fallback(tmp_config: TemporaryConfiguration,
                                        monkeypatch: MonkeyPatch,
                                        url: str) -> None:
    """When BibTeX fetch is blocked, the importer fetches the PDF bytes
    privately, parses a DOI, and queries Crossref. ``ctx.files`` must stay
    empty (no private temp file leaks)."""
    from papis.importer.ieee import IEEEImporter

    imp = IEEEImporter.match(url)
    assert isinstance(imp, IEEEImporter)

    down = imp._downloader
    # Simulate IEEE blocking the metadata API (empty BibTeX).
    monkeypatch.setattr(down, "download_bibtex",
                        lambda: setattr(down, "bibtex_data", ""))
    monkeypatch.setattr(down, "get_data", lambda: {})

    # The private PDF fetch must NOT cycle through fetch_files / ctx.files.
    def _fail_fetch_files() -> None:
        raise AssertionError(
            "fetch_data must not call fetch_files; it should use "
            "get_document_data directly")
    monkeypatch.setattr(down, "fetch_files", _fail_fetch_files)

    # Pretend the private PDF fetch returned bytes. _extract_doi_from_pdf
    # writes them to a temp file internally, which _doi_from_pdf reads.
    monkeypatch.setattr(down, "get_document_data", lambda: b"%PDF-1.4 fake")
    monkeypatch.setattr(IEEEImporter, "_doi_from_pdf",
                        staticmethod(lambda p: "10.1109/TEST.2023.10301652"))
    monkeypatch.setattr(IEEEImporter, "_crossref_data",
                        staticmethod(lambda d: {
                            "title": "Reliable Multi-Path RPL for IoT",
                            "author": "Doe, Jane",
                            "year": 2023,
                            "doi": d,
                        }))

    imp.fetch_data()
    assert imp.ctx.data["doi"] == "10.1109/TEST.2023.10301652"
    assert imp.ctx.data["title"] == "Reliable Multi-Path RPL for IoT"
    # Critical: metadata-only import must not leave files in ctx.
    assert imp.ctx.files == []


def test_ieee_importer_no_pdf_access(tmp_config: TemporaryConfiguration,
                                     monkeypatch: MonkeyPatch) -> None:
    """When both BibTeX and PDF download fail (no institutional access), the
    importer logs an institutional-access warning and leaves ctx empty; the
    Crossref fallback is never reached."""
    from papis.importer.ieee import IEEEImporter

    url = "https://ieeexplore.ieee.org/document/10301652"
    imp = IEEEImporter.match(url)
    assert isinstance(imp, IEEEImporter)

    down = imp._downloader
    monkeypatch.setattr(down, "download_bibtex",
                        lambda: setattr(down, "bibtex_data", ""))
    monkeypatch.setattr(down, "get_data", lambda: {})
    # The private PDF fetch returns no bytes -> fallback gives up.
    monkeypatch.setattr(down, "get_document_data", lambda: None)

    def _fail_crossref(_doi: str) -> dict[str, Any] | None:
        raise AssertionError("Crossref must not be queried when no PDF")
    monkeypatch.setattr(IEEEImporter, "_crossref_data",
                        staticmethod(_fail_crossref))

    imp.fetch_data()
    assert imp.ctx.data == {}
    assert imp.ctx.files == []


def test_ieee_importer_doi_found_no_crossref(
        tmp_config: TemporaryConfiguration,
        monkeypatch: MonkeyPatch) -> None:
    """When a DOI is parsed but Crossref has no record, ctx.data stays empty
    and a distinct Crossref-failure warning is logged."""
    from papis.importer.ieee import IEEEImporter

    url = "https://ieeexplore.ieee.org/document/10301652"
    imp = IEEEImporter.match(url)
    assert isinstance(imp, IEEEImporter)

    down = imp._downloader
    monkeypatch.setattr(down, "download_bibtex",
                        lambda: setattr(down, "bibtex_data", ""))
    monkeypatch.setattr(down, "get_data", lambda: {})
    monkeypatch.setattr(down, "get_document_data", lambda: b"%PDF-1.4 fake")
    monkeypatch.setattr(IEEEImporter, "_doi_from_pdf",
                        staticmethod(lambda p: "10.1109/NOPE.2023.9999999"))
    monkeypatch.setattr(IEEEImporter, "_crossref_data",
                        staticmethod(lambda d: None))

    imp.fetch_data()
    assert imp.ctx.data == {}
    assert imp.ctx.files == []


def test_ieee_doi_from_pdf_bare(tmp_config: TemporaryConfiguration,
                                tmp_path: object) -> None:
    """_doi_from_pdf scans raw bytes for a bare DOI when pdf_to_doi misses it.

    IEEE PDFs embed the DOI in /Subject without a "doi:" prefix, which the
    upstream ``doi.pdf_to_doi`` requires. This mirrors the IEEE PDF metadata
    line that exists in the real downloaded file.
    """
    import pathlib

    from papis.importer.ieee import IEEEImporter

    pdf = pathlib.Path(str(tmp_path)) / "fake.pdf"
    pdf.write_bytes(
        b"%PDF-1.4\n"
        b"/Subject (IEEE Transactions on Mobile Computing;"
        b"2024;23;6;10.1109/TMC.2023.3328346)\n"
        b"%%EOF\n"
    )

    doi = IEEEImporter._doi_from_pdf(str(pdf))
    assert doi == "10.1109/TMC.2023.3328346"


def test_ieee_doi_from_pdf_scan_is_capped(
        tmp_config: TemporaryConfiguration,
        tmp_path: object) -> None:
    """The byte-scan fallback is capped at _DOI_SCAN_MAXLINES lines so that
    large PDFs cannot be parsed end-to-end just to find a DOI."""
    import pathlib

    from papis.importer.ieee import IEEEImporter

    # Put a DOI well past the scan cap to ensure the scan does not reach it.
    # Note: ``pdf_to_doi`` would also fail (no "doi:" prefix), so the only
    # way to find this DOI is the unbounded byte scan we want to bound.
    filler_line = b"x" * 8 + b"\n"
    pdf = pathlib.Path(str(tmp_path)) / "fake.pdf"
    pdf.write_bytes(
        b"%PDF-1.4\n"
        + filler_line * 300
        + b"10.1109/TMC.2023.3328346\n"
    )

    assert IEEEImporter._doi_from_pdf(str(pdf)) is None
