"""Tests for the client-side gather stage."""

from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING

import pytest
import requests

import papis.gather as gather_module
import papis.utils
from papis.gather import (
    fetch_metadata_content,
    gather,
    read_content,
    register_extractor,
)

if TYPE_CHECKING:
    from typing import Any, Literal

    from papis.testing import TemporaryConfiguration, TemporaryLibrary


def test_gather_bare_string() -> None:
    item = gather("10.1103/PhysRevLett.123.156401")
    assert item.evidence.input == "10.1103/PhysRevLett.123.156401"
    assert item.evidence.content is None
    assert item.evidence.fields == {}
    assert item.local_files == []


def test_gather_strips_input() -> None:
    item = gather("  10.1103/PhysRevLett.123.156401  ")
    assert item.evidence.input == "10.1103/PhysRevLett.123.156401"


def test_gather_strips_input_before_classification(tmp_path: Any) -> None:
    # NOTE: the strip happens before the path/URL triage, so a padded path is
    # still read as a file instead of falling through to the bare-input case
    path = tmp_path / "example.bib"
    path.write_text("@article{key, title = {A title}}", encoding="utf-8")

    item = gather(f"  {path}  ")
    assert item.evidence.input == str(path)
    assert item.evidence.content is not None
    assert item.local_files == [str(path)]


def test_gather_text_file(tmp_path: Any) -> None:
    path = tmp_path / "example.bib"
    path.write_text("@article{key, title = {A title}}", encoding="utf-8")

    item = gather(str(path))
    assert item.evidence.input == str(path)
    assert item.evidence.kind == "file"
    assert item.evidence.content is not None
    assert "@article" in item.evidence.content
    assert item.local_files == [str(path)]


def test_gather_binary_file(tmp_path: Any) -> None:
    # NOTE: text-ness is decided by decoding alone (see 'inspect_file')
    path = tmp_path / "paper.epub"
    path.write_bytes(b"\xff\xfe\x02binary")

    item = gather(str(path))
    assert item.evidence.content is None
    assert item.evidence.fields == {}
    assert item.local_files == [str(path)]


def test_gather_decodable_content_is_not_judged(tmp_path: Any) -> None:
    # NOTE: a decodable-but-not-text payload is passed through as content:
    # content-format handlers decline it by parsing
    path = tmp_path / "paper.bin"
    path.write_bytes(b"\x00\x01\x02binary")

    item = gather(str(path))
    assert item.evidence.content == "\x00\x01\x02binary"


def test_read_content(tmp_path: Any) -> None:
    """Text files are read; binary files have no text content."""
    path = tmp_path / "example.bib"
    path.write_text("@article{key, title = {A title}}", encoding="utf-8")
    assert read_content(str(path)) == "@article{key, title = {A title}}"

    binary = tmp_path / "paper.epub"
    binary.write_bytes(b"\xff\xfe\x02binary")
    assert read_content(str(binary)) is None


def test_gather_pdf_extractors(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gather_module, "_EXTRACTORS", {})
    register_extractor("pdf", lambda path: {"doi": "10.1103/physrevb.89"})
    register_extractor(
        "pdf", lambda path: {"eprint": "1110.3658", "eprinttype": "arxiv"}
    )

    path = tmp_path / "paper.pdf"
    path.write_bytes(b"fake pdf")

    item = gather(str(path))
    assert item.evidence.fields == {
        "doi": "10.1103/physrevb.89",
        "eprint": "1110.3658",
        "eprinttype": "arxiv",
    }
    assert item.local_files == [str(path)]


def test_gather_pdf_arxiv_extractor(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The arXiv extractor emits the same BibLaTeX fields as the source."""
    monkeypatch.setattr(
        gather_module, "_EXTRACTORS", {"pdf": [gather_module._extract_pdf_arxivid]}
    )
    monkeypatch.setattr(
        "papis.arxiv.pdf_to_arxivid", lambda path, maxlines: "1110.3658"
    )

    path = tmp_path / "paper.pdf"
    path.write_bytes(b"fake pdf")

    item = gather(str(path))
    assert item.evidence.fields == {
        "eprint": "1110.3658",
        "eprinttype": "arxiv",
    }


def test_gather_pdf_extractor_failure(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gather_module, "_EXTRACTORS", {})

    def _fail(path: str) -> dict[str, Any]:
        raise RuntimeError("boom")

    register_extractor("pdf", _fail)

    path = tmp_path / "paper.pdf"
    path.write_bytes(b"fake pdf")

    item = gather(str(path))
    assert item.evidence.fields == {}
    assert item.local_files == [str(path)]


def test_gather_directory(tmp_library: TemporaryLibrary) -> None:
    from papis.testing import create_random_file
    from papis.yaml import data_to_yaml

    folder = os.path.join(tmp_library.tmpdir, "test-gather-folder")
    os.makedirs(folder)

    file_path = create_random_file(dir=folder)
    data_to_yaml(
        os.path.join(folder, "info.yaml"),
        {
            "author": "Plato",
            "title": "Republic",
            "files": [os.path.basename(file_path)],
        },
    )

    item = gather(folder)
    assert item.evidence.input == folder
    # NOTE: a directory is just a string to source handlers; its contents
    # belong to the 'folder' client source (see 'papis.sources.client' and
    # 'tests/sources/test_client.py')
    assert item.evidence.fields == {}
    assert item.local_files == []


class _FakeSession:
    def __init__(
        self,
        ok: bool = True,
        content: bytes = b"",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.ok = ok
        self.content = content
        self.headers = headers or {}
        self.status_code = 200 if ok else 404
        self.reason = "Not Found" if not ok else "OK"

    def get(self, url: str, timeout: int | None = None) -> _FakeSession:
        self.url = url
        return self

    def __enter__(self) -> _FakeSession:
        return self

    def __exit__(self, *args: Any) -> Literal[False]:
        return False


def test_gather_url_page(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        papis.utils,
        "get_session",
        lambda: _FakeSession(
            content=b"<html><title>Paper</title></html>",
            headers={"Content-Type": "text/html; charset=utf-8"},
        ),
    )

    item = gather("https://journals.aps.org/prl/abstract/10.1103/x")
    assert item.evidence.input.startswith("https://")
    assert item.evidence.kind == "webpage"
    assert item.evidence.content is not None
    assert "<html>" in item.evidence.content
    assert item.local_files == []


@pytest.mark.parametrize(
    ("headers", "content", "expected_kind"),
    [
        # files are not web pages, whatever the URL looks like
        ({"Content-Type": "application/x-bibtex"}, b"@article{key}", "file"),
        ({"Content-Type": "text/plain"}, b"@article{key}", "file"),
        ({"Content-Type": "application/pdf"}, b"%PDF-1.4", "file"),
        # a page is a page even when the server offers it as a download
        (
            {
                "Content-Type": "text/html",
                "Content-Disposition": 'attachment; filename="paper.pdf"',
            },
            b"<html>consent</html>",
            "webpage",
        ),
        # without a content type, the response is treated as a file
        ({}, b"<!DOCTYPE html><html></html>", "file"),
        ({}, b"@article{key}", "file"),
    ],
)
def test_gather_url_classifies_response(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
    headers: dict[str, str],
    content: bytes,
    expected_kind: str,
) -> None:
    """A response is a page or a file according to its Content-Type. Only files
    are attached."""
    stored = tmp_path / "stored"
    stored.write_bytes(content)
    monkeypatch.setattr(gather_module, "_EXTRACTORS", {})
    monkeypatch.setattr(gather_module, "_store_response", lambda response: str(stored))
    monkeypatch.setattr(
        papis.utils,
        "get_session",
        lambda: _FakeSession(content=content, headers=headers),
    )

    item = gather("https://example.com/export/12345")
    assert item.evidence.kind == expected_kind
    assert item.local_files == ([str(stored)] if expected_kind == "file" else [])


def test_gather_url_failure(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(papis.utils, "get_session", lambda: _FakeSession(ok=False))

    item = gather("https://example.com/nope")
    assert item.evidence.input == "https://example.com/nope"
    assert item.evidence.content is None
    assert "Could not fetch" in caplog.text


def test_gather_url_transport_failure_is_error(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A network failure is logged as an error: the user asked for this URL."""

    def _fail_session() -> _FakeSession:
        raise requests.exceptions.ConnectionError("connection refused")

    monkeypatch.setattr(papis.utils, "get_session", _fail_session)

    with caplog.at_level("DEBUG"):
        item = gather("https://example.com/nope")

    assert item.evidence.input == "https://example.com/nope"
    assert item.evidence.content is None

    assert any(
        r.levelname == "ERROR" and "Could not fetch" in r.message
        for r in caplog.records
    )


def test_gather_url_unexpected_failure_is_error(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A non-transport failure is a bug: error, still isolated to the input."""

    def _fail_session() -> _FakeSession:
        raise RuntimeError("bug")

    monkeypatch.setattr(papis.utils, "get_session", _fail_session)

    with caplog.at_level("DEBUG"):
        item = gather("https://example.com/nope")

    assert item.evidence.input == "https://example.com/nope"
    assert item.evidence.content is None

    assert any(
        r.levelname == "ERROR" and "unexpectedly" in r.message for r in caplog.records
    )


def test_gather_url_document_response_is_attached(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A document file response is downloaded and attached, whatever the URL
    looks like (e.g. an extension-less arXiv PDF link)."""
    monkeypatch.setattr(gather_module, "_EXTRACTORS", {})
    monkeypatch.setattr(
        papis.utils,
        "get_session",
        lambda: _FakeSession(
            content=b"%PDF-1.4\xff\xfe binary",
            headers={"Content-Type": "application/pdf"},
        ),
    )

    item = gather("https://arxiv.org/pdf/2408.03952")
    assert item.evidence.kind == "file"
    assert item.evidence.content is None
    assert item.evidence.fields == {}
    assert len(item.local_files) == 1
    os.remove(item.local_files[0])


def test_gather_url_page_response_for_document_url_is_a_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A page served where a document is expected is a page: the response
    decides, not the URL."""
    monkeypatch.setattr(
        papis.utils,
        "get_session",
        lambda: _FakeSession(
            content=b"<html>consent</html>", headers={"Content-Type": "text/html"}
        ),
    )

    item = gather("https://example.com/paper.pdf")
    assert item.evidence.kind == "webpage"
    assert item.evidence.content is not None
    assert item.local_files == []


def test_gather_url_request_failure_is_bare_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed download falls through to the bare input: no second fetch."""
    calls: list[str] = []

    def _fail_request(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        return None

    monkeypatch.setattr(gather_module, "_request", _fail_request)

    item = gather("https://example.com/paper.pdf")
    assert calls == ["https://example.com/paper.pdf"]
    assert item.evidence.content is None
    assert item.local_files == []


@pytest.mark.parametrize(
    ("url", "content", "content_type", "expected_file_name"),
    [
        # the URL path names the file and the content type gives it an extension
        (
            "https://arxiv.org/pdf/2408.03952",
            b"%PDF-1.4 fake",
            "application/pdf",
            "2408.03952.pdf",
        ),
        # nothing in the path to go by: the host names the file
        (
            "https://github.com/",
            b"<html><body></body></html>",
            "text/html",
            "github.com.html",
        ),
    ],
)
def test_download_document_names_the_file(
    tmp_config: TemporaryConfiguration,
    monkeypatch: pytest.MonkeyPatch,
    url: str,
    content: bytes,
    content_type: str,
    expected_file_name: str,
) -> None:
    """A downloaded file is named from the response alone (no live server)."""
    import papis.utils
    from papis.gather import download_document

    class FakeResponse:
        ok = True
        status_code = 200
        reason = "OK"

        def __init__(self) -> None:
            self.url = url
            self.content = content
            self.headers = {"Content-Type": content_type}

    class FakeSession:
        def __init__(self) -> None:
            self.response = FakeResponse()

        def get(self, *args: object, **kwargs: object) -> FakeResponse:
            return self.response

        def __enter__(self) -> FakeSession:
            return self

        def __exit__(self, *args: object) -> Literal[False]:
            return False

    monkeypatch.setattr(papis.utils, "get_session", FakeSession)

    local_file_name = download_document(url)
    assert local_file_name is not None

    # NOTE: a stale earlier download in the temp dir makes `make_unique_file`
    # add a '-<letters>' suffix; accept it instead of clobbering the old file
    root, file_ext = os.path.splitext(expected_file_name)
    assert re.fullmatch(
        rf"{re.escape(root)}(-[a-z]+)?{re.escape(file_ext)}",
        os.path.basename(local_file_name),
    ), os.path.basename(local_file_name)

    os.remove(local_file_name)


def test_fetch_metadata_content_rejects_html(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A page is not a metadata file: a bot block or consent screen must not be
    handed to a format handler."""
    url = "https://example.com/download/1234"
    monkeypatch.setattr(
        papis.utils,
        "get_session",
        lambda: _FakeSession(
            content=b"<html>Just a moment...</html>",
            headers={
                "Content-Type": "text/html",
                "Content-Disposition": 'attachment; filename="refs.bib"',
            },
        ),
    )
    assert fetch_metadata_content(url) is None

    monkeypatch.setattr(
        papis.utils,
        "get_session",
        lambda: _FakeSession(
            content=b"@article{key}", headers={"Content-Type": "application/x-bibtex"}
        ),
    )
    assert fetch_metadata_content(url) == "@article{key}"


def test_download_document_expected_extension(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An expected extension (see ``FileReference.extension``) rejects payloads
    that are confidently another type (e.g. an HTML error page) and accepts
    inconclusive ones."""
    import papis.utils

    class FakeResponse:
        ok = True
        status_code = 200
        reason = "OK"
        url = "https://example.com/paper.pdf"

        def __init__(self, content: bytes, content_type: str | None) -> None:
            self.content = content
            self.headers = {"Content-Type": content_type} if content_type else {}

    class FakeSession:
        def __init__(self, response: FakeResponse) -> None:
            self.response = response

        def get(self, *args: object, **kwargs: object) -> FakeResponse:
            return self.response

        def __enter__(self) -> FakeSession:
            return self

        def __exit__(self, *args: object) -> Literal[False]:
            return False

    from papis.gather import download_document

    # a page served in place of the PDF is rejected
    html = FakeResponse(b"<html><body>consent</body></html>", "text/html")
    monkeypatch.setattr(papis.utils, "get_session", lambda: FakeSession(html))
    assert (
        download_document(
            "https://example.com/paper.pdf", expected_document_extension="pdf"
        )
        is None
    )

    # a generic Content-Type does not hide the real (guessed) type
    pdf = FakeResponse(b"%PDF-1.4 fake", "application/octet-stream")
    monkeypatch.setattr(papis.utils, "get_session", lambda: FakeSession(pdf))

    path = download_document(
        "https://example.com/paper.pdf", expected_document_extension="pdf"
    )
    assert path is not None
    os.remove(path)

    # no usable hint at all: the payload is accepted
    unknown = FakeResponse(b"some plain text", content_type=None)
    monkeypatch.setattr(papis.utils, "get_session", lambda: FakeSession(unknown))

    path = download_document(
        "https://example.com/paper.pdf", expected_document_extension="pdf"
    )
    assert path is not None
    os.remove(path)

    # a dotted or uppercase expected extension is normalized at the boundary
    monkeypatch.setattr(papis.utils, "get_session", lambda: FakeSession(pdf))

    path = download_document(
        "https://example.com/paper.pdf", expected_document_extension=".PDF"
    )
    assert path is not None
    assert path.endswith(".pdf")
    os.remove(path)


def test_download_document_filename_without_extension_sniffs_type(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A suggested filename without an extension does not hide the sniffed type."""
    import papis.utils
    from papis.gather import download_document

    class FakeResponse:
        ok = True
        status_code = 200
        reason = "OK"
        url = "https://example.com/download"
        content = b"%PDF-1.4 fake"

        def __init__(self) -> None:
            self.headers = {"Content-Disposition": 'attachment; filename="paper"'}

    class FakeSession:
        def __init__(self) -> None:
            self.response = FakeResponse()

        def get(self, *args: object, **kwargs: object) -> FakeResponse:
            return self.response

        def __enter__(self) -> FakeSession:
            return self

        def __exit__(self, *args: object) -> Literal[False]:
            return False

    monkeypatch.setattr(papis.utils, "get_session", FakeSession)

    path = download_document("https://example.com/download")
    assert path is not None
    assert os.path.basename(path).startswith("paper")
    assert path.endswith(".pdf")
    os.remove(path)


def test_download_document_transport_failure_is_error(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A document papis cannot deliver is a failure, not expected operation."""
    import papis.utils
    from papis.gather import download_document

    def _fail_session() -> None:
        raise requests.exceptions.ConnectionError("network down")

    monkeypatch.setattr(papis.utils, "get_session", _fail_session)

    with caplog.at_level("DEBUG"):
        path = download_document("https://example.com/paper.pdf")

    assert path is None
    assert any(
        r.levelname == "ERROR" and "Could not fetch" in r.message
        for r in caplog.records
    )


@pytest.mark.parametrize(
    ("headers", "content", "expected_content"),
    [
        # the text of a metadata file is evidence, like a local file's
        (
            {"Content-Type": "application/x-bibtex"},
            b"@article{key, title = {A title}}",
            "@article{key, title = {A title}}",
        ),
        # a binary payload has no text to parse
        (
            {"Content-Type": "application/octet-stream"},
            b"%PDF-1.4\xff\xfe binary",
            None,
        ),
        # an uncompressed PDF is all ASCII, but it is still a document
        (
            {"Content-Type": "application/pdf"},
            b"%PDF-1.4 uncompressed",
            "%PDF-1.4 uncompressed",
        ),
    ],
)
def test_gather_url_file_content(
    monkeypatch: pytest.MonkeyPatch,
    headers: dict[str, str],
    content: bytes,
    expected_content: str | None,
) -> None:
    """A file gathered from a URL is attached like a local file, and its text (if
    any) is read as evidence."""
    monkeypatch.setattr(gather_module, "_EXTRACTORS", {})
    monkeypatch.setattr(
        papis.utils,
        "get_session",
        lambda: _FakeSession(content=content, headers=headers),
    )

    item = gather("https://example.com/download/12345")
    assert item.evidence.kind == "file"
    assert item.evidence.content == expected_content
    assert item.evidence.fields == {}
    assert len(item.local_files) == 1
    os.remove(item.local_files[0])
