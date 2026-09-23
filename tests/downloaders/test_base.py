"""Tests for the legacy ``Downloader`` plugin base class.

The site-specific downloaders are native source handlers now; this module pins
down the base-class behavior that third-party downloader plugins rely on.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest
import requests

import papis.gather
from papis.downloaders import Downloader

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


def _response(
        content: bytes,
        *,
        url: str = "https://example.org/article",
        headers: dict[str, str] | None = None,
        ) -> requests.Response:
    """Build a response with the bits that :class:`Downloader` reads."""
    response = requests.Response()
    response.status_code = 200
    response.url = url
    response.headers.update(headers or {})
    response._content = content

    return response


class FakeSession(requests.Session):
    """A session whose ``get`` pops queued responses instead of networking."""

    def __init__(self, *responses: requests.Response) -> None:
        super().__init__()
        self.queued = list(responses)
        self.calls: list[dict[str, Any]] = []

    def get(self, url: str | bytes, **kwargs: Any) -> requests.Response:
        self.calls.append({"url": url, **kwargs})
        return self.queued.pop(0)


class DocumentDownloader(Downloader):
    """A downloader with a document URL, as a scraping plugin would have."""

    name = "document"

    def get_document_url(self) -> str:  # ruff: ignore[no-self-use]
        return "https://example.org/paper.pdf"


class NoUrlDownloader(Downloader):
    """A downloader whose document URL is unknown."""

    name = "nourl"

    def get_document_url(self) -> None:  # ruff: ignore[no-self-use]
        return None


class BibtexDownloader(Downloader):
    """A downloader implementing the scrape/BibTeX/DOI hooks of ``fetch_data``."""

    name = "bibtex"

    def get_data(self) -> dict[str, Any]:  # ruff: ignore[no-self-use]
        # NOTE: the BibTeX data and the DOI are expected to overwrite the
        # values scraped from the page
        return {"title": "Scraped", "journal": "Scraped Journal"}

    def get_bibtex_url(self) -> str:  # ruff: ignore[no-self-use]
        return "https://example.org/article.bib"

    def get_doi(self) -> str:  # ruff: ignore[no-self-use]
        return "10.1/from-get-doi"


@pytest.fixture
def session(monkeypatch: pytest.MonkeyPatch) -> FakeSession:
    """Route ``Downloader`` session creation to a fake session."""
    session = FakeSession()
    monkeypatch.setattr("papis.utils.get_session", lambda: session)
    return session


@pytest.fixture
def downloader(session: FakeSession) -> Downloader:
    return Downloader(uri="https://example.org/article", name="fake")


def test_downloader_defaults_raise(downloader: Downloader) -> None:
    """The optional hooks raise, matching the documented plugin contract."""
    with pytest.raises(NotImplementedError):
        downloader.get_bibtex_url()

    with pytest.raises(NotImplementedError):
        downloader.get_data()

    with pytest.raises(NotImplementedError):
        downloader.get_doi()

    with pytest.raises(NotImplementedError):
        downloader.get_document_url()

    with pytest.raises(NotImplementedError):
        type(downloader).match("https://example.org/article")


def test_fetch_defaults_are_noop(downloader: Downloader) -> None:
    """A downloader implementing nothing fetches nothing, without raising."""
    downloader.fetch_data()
    downloader.fetch_files()
    downloader.fetch()

    assert not downloader.ctx


def test_downloader_str(downloader: Downloader) -> None:
    assert str(downloader) == (
        "Downloader(fake, uri=https://example.org/article)")


@pytest.mark.parametrize(("extension", "expected"), [
    (None, None),
    ("pdf", ("pdf",)),
    (["pdf"], ("pdf",)),
    (("pdf", "djvu"), ("pdf", "djvu")),
])
def test_downloader_extension_normalization(
        session: FakeSession,
        extension: str | Sequence[str] | None,
        expected: tuple[str, ...] | None) -> None:
    """A single extension is normalized to a tuple, as documented."""
    down = Downloader(
        expected_document_extension=extension,
        cookies={"a": "b"},
        priority=7,
    )
    assert down.expected_document_extensions == expected
    assert down.cookies == {"a": "b"}
    assert down.priority == 7


def test_get_body(session: FakeSession, downloader: Downloader) -> None:
    session.queued.append(_response(b"body"))

    assert downloader._get_body() == b"body"
    assert session.calls == [{
        "url": "https://example.org/article",
        "cookies": {},
    }]


def test_get_soup_caches(session: FakeSession, downloader: Downloader) -> None:
    html = b"<html><body><h1>Hello</h1></body></html>"
    session.queued.append(_response(html))

    soup = downloader._get_soup()
    assert soup.h1 is not None
    assert soup.h1.string == "Hello"

    # the parsed soup is cached: no further request is made
    assert downloader._get_soup() is soup
    assert len(session.calls) == 1


def test_download_bibtex(
        session: FakeSession,
        downloader: Downloader,
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        downloader, "get_bibtex_url",
        lambda: "https://example.org/article.bib")
    session.queued.append(_response(b"@article{key, title={Bib}}"))

    downloader.download_bibtex()
    assert downloader.bibtex_data == "@article{key, title={Bib}}"
    assert session.calls == [{
        "url": "https://example.org/article.bib",
        "cookies": {},
    }]


def test_download_bibtex_no_url(
        session: FakeSession,
        downloader: Downloader,
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(downloader, "get_bibtex_url", lambda: None)

    downloader.download_bibtex()
    assert downloader.bibtex_data is None
    assert session.calls == []


def test_get_bibtex_data_cached(
        downloader: Downloader,
        monkeypatch: pytest.MonkeyPatch) -> None:
    called = []

    def _download() -> None:
        called.append("download")
        downloader.bibtex_data = "cached"

    monkeypatch.setattr(downloader, "download_bibtex", _download)

    assert downloader.get_bibtex_data() == "cached"
    assert downloader.get_bibtex_data() == "cached"
    assert called == ["download"]


def test_get_bibtex_data_downloads(
        session: FakeSession,
        downloader: Downloader,
        monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        downloader, "get_bibtex_url",
        lambda: "https://example.org/article.bib")
    session.queued.append(_response(b"bib"))

    assert downloader.get_bibtex_data() == "bib"


def test_fetch_data_merges_hooks(session: FakeSession) -> None:
    """Scraped data, BibTeX and DOI are merged in the documented order."""
    down = BibtexDownloader(uri="https://example.org/article", name="bibtex")
    session.queued.append(_response(b"@article{key, title = {From BibTeX}}"))

    down.fetch_data()
    assert down.ctx.data["journal"] == "Scraped Journal"
    assert down.ctx.data["title"] == "From BibTeX"
    assert down.ctx.data["doi"] == "10.1/from-get-doi"


def test_fetch_data_picks_first_bibtex_entry(
        session: FakeSession,
        caplog: pytest.LogCaptureFixture) -> None:
    """Multi-entry BibTeX data is truncated to the first entry."""
    down = BibtexDownloader(uri="https://example.org/article", name="bibtex")
    session.queued.append(_response(b"""
        @article{one, title = {First}}
        @article{two, title = {Second}}
        """))

    with caplog.at_level("WARNING", logger="papis.downloader.bibtex"):
        down.fetch_data()

    assert down.ctx.data["title"] == "First"
    assert any(
        record.levelname == "WARNING"
        and "found 2 BibTeX entries" in record.message
        for record in caplog.records)


def test_download_document(session: FakeSession) -> None:
    down = DocumentDownloader(uri="https://example.org/article", name="document")
    session.queued.append(_response(
        b"data",
        headers={"Content-Disposition": 'attachment; filename="paper.pdf"'},
    ))

    down.download_document()
    assert down.document_filename == "paper.pdf"
    assert down.document_data == b"data"
    assert session.calls == [{
        "url": "https://example.org/paper.pdf",
        "cookies": {},
    }]


def test_download_document_no_url(session: FakeSession) -> None:
    down = NoUrlDownloader(uri="https://example.org/article", name="nourl")

    down.download_document()
    assert down.document_data is None
    assert session.calls == []


def test_get_document_data_downloads(session: FakeSession) -> None:
    down = DocumentDownloader(uri="https://example.org/article", name="document")
    session.queued.append(_response(b"data"))

    assert down.get_document_data() == b"data"


def test_get_document_data_cached(
        downloader: Downloader,
        monkeypatch: pytest.MonkeyPatch) -> None:
    def _download() -> None:
        raise AssertionError("cached data must not be downloaded again")

    monkeypatch.setattr(downloader, "download_document", _download)
    downloader.document_data = b"cached"

    assert downloader.get_document_data() == b"cached"


@pytest.mark.parametrize(("expected", "extension", "result"), [
    (None, "pdf", True),
    (("pdf",), "pdf", True),
    (("pdf", "djvu"), "djvu", True),
    (("pdf",), "html", False),
    (("pdf",), "", False),
])
def test_check_document_format(
        session: FakeSession,
        expected: tuple[str, ...] | None,
        extension: str,
        result: bool) -> None:
    down = Downloader(expected_document_extension=expected)
    down.document_extension = extension

    assert down.check_document_format() is result


def test_get_document_extension_from_filename(
        session: FakeSession,
        downloader: Downloader) -> None:
    downloader.document_filename = "paper.pdf"

    assert downloader.get_document_extension() == "pdf"
    assert downloader.document_extension == "pdf"


def test_get_document_extension_cached(
        downloader: Downloader) -> None:
    downloader.document_extension = "djvu"

    assert downloader.get_document_extension() == "djvu"
    assert downloader.document_data is None


def test_get_document_extension_from_content(
        downloader: Downloader) -> None:
    downloader.document_data = b"%PDF-1.4 fake"

    assert downloader.get_document_extension() == "pdf"
    assert downloader.document_extension == "pdf"


def test_get_document_extension_no_data(session: FakeSession) -> None:
    down = NoUrlDownloader(uri="https://example.org/article", name="nourl")

    assert down.get_document_extension() == ""
    assert down.document_extension == ""


def test_fetch_files_from_response_filename(
        session: FakeSession,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path) -> None:
    monkeypatch.setattr(
        papis.gather, "_TEMP_DIR", SimpleNamespace(name=str(tmp_path)))

    down = DocumentDownloader(
        uri="https://example.org/article",
        name="document",
        expected_document_extension="pdf",
    )
    session.queued.append(_response(
        b"%PDF-1.4 fake",
        headers={"Content-Disposition": 'attachment; filename="paper.pdf"'},
    ))

    down.fetch_files()
    [filename] = down.ctx.files
    assert filename == str(tmp_path / "paper.pdf")
    with open(filename, "rb") as fd:
        assert fd.read() == b"%PDF-1.4 fake"


def test_fetch_files_guesses_extension_from_content(
        session: FakeSession,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path) -> None:
    monkeypatch.setattr(
        papis.gather, "_TEMP_DIR", SimpleNamespace(name=str(tmp_path)))

    down = DocumentDownloader(
        uri="https://example.org/article",
        name="document",
        expected_document_extension="pdf",
    )
    session.queued.append(
        _response(b"%PDF-1.4 fake", url="https://example.org/download"))

    down.fetch_files()
    [filename] = down.ctx.files
    assert filename.startswith(str(tmp_path))
    assert filename.endswith(".pdf")
    with open(filename, "rb") as fd:
        assert fd.read() == b"%PDF-1.4 fake"


def test_fetch_files_rejects_unexpected_format(
        session: FakeSession,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture) -> None:
    monkeypatch.setattr("tempfile.tempdir", str(tmp_path))

    down = DocumentDownloader(
        uri="https://example.org/article",
        name="document",
        expected_document_extension="pdf",
    )
    session.queued.append(_response(
        b"<html>not a pdf</html>",
        headers={"Content-Disposition": 'attachment; filename="paper.html"'},
    ))

    with caplog.at_level("ERROR", logger="papis.downloader.document"):
        down.fetch_files()

    assert down.ctx.files == []
    assert any(
        record.levelname == "ERROR" and "expected types" in record.message
        for record in caplog.records)


def test_fetch_calls_data_and_files_once(
        downloader: Downloader,
        monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def _fetch_data() -> None:
        calls.append("data")
        downloader.ctx.data["title"] = "Fetched"

    def _fetch_files() -> None:
        calls.append("files")

    monkeypatch.setattr(downloader, "fetch_data", _fetch_data)
    monkeypatch.setattr(downloader, "fetch_files", _fetch_files)

    downloader.fetch()
    # the context is populated, so the cached fetch is a no-op
    downloader.fetch()
    assert calls == ["data", "files"]
