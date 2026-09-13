from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import pytest
import requests

if TYPE_CHECKING:
    from collections.abc import Callable

    from papis.testing import TemporaryConfiguration


def load_json(filename: str, data_getter: Callable[[], Any] | None = None) -> Any:
    import json
    path = os.path.join(
        os.path.dirname(__file__), "resources", "isbn", filename)

    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    elif data_getter is not None:
        data = data_getter()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, sort_keys=True)
    else:
        raise ValueError("Must provide a filename or a getter")

    return data


def get_unmodified_isbn_data(query: str) -> Any:
    from papis.isbn import isbn_from_words, meta

    isbn = isbn_from_words(query)
    data = meta(isbn, service="openl")
    assert data is not None

    return data


@pytest.mark.xfail(reason="sometimes makes too many requests")
def test_get_data(tmp_config: TemporaryConfiguration) -> None:
    from papis.isbn import get_data

    result = get_data(query="Mattuck feynan diagrams")
    assert result
    assert isinstance(result, list)
    assert isinstance(result[0], dict)
    assert result[0]["isbn-13"] == "9780486670478"
    assert result[0]["language"] != ""


def test_importer_match(tmp_config: TemporaryConfiguration) -> None:
    from papis.importer.isbn import ISBNImporter

    assert ISBNImporter.match("9780486670478")
    assert ISBNImporter.match("this-is-not-an-isbn") is None

    # NOTE: ISBN for Wesseling - An Introduction to Multigrid Methods
    importer = ISBNImporter.match("9781930217089")
    assert importer
    assert importer.uri == "9781930217089"


@pytest.mark.parametrize("basename", ["test_isbn_1"])
def test_isbn_to_papis(tmp_config: TemporaryConfiguration, basename: str) -> None:
    from papis.isbn import data_to_papis

    data = load_json(
        f"{basename}.json",
        data_getter=lambda: get_unmodified_isbn_data("9781930217089"))

    to_papis_data = data_to_papis(data)
    result = load_json(
        f"{basename}_out.json",
        data_getter=lambda: to_papis_data)

    assert to_papis_data == result


def _fake_response(status_code: int = 200, content: bytes = b"") -> Any:
    """Return a replacement for ``requests.Session.get``."""
    def get(self: Any, url: str, **kwargs: Any) -> requests.Response:
        response = requests.Response()
        response.url = url
        response.status_code = status_code
        response._content = content
        return response

    return get


def test_json_request_not_found(tmp_config: TemporaryConfiguration,
                                monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.isbn
    from papis.exceptions import SourceError

    monkeypatch.setattr(requests.Session, "get", _fake_response(404))

    # NOTE: query endpoints report a missing entry with a 200 and an empty
    # envelope, so a 404 from them means the URL is broken
    with pytest.raises(SourceError, match="Could not query"):
        papis.isbn.json_request("https://example.com")


def test_json_request_not_found_as_absent(
        tmp_config: TemporaryConfiguration,
        monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.isbn

    monkeypatch.setattr(requests.Session, "get", _fake_response(404))

    assert papis.isbn.json_request(
        "https://example.com", http_not_found_is_absent=True) is None


def test_meta_wiki_missing_isbn(tmp_config: TemporaryConfiguration,
                                monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.isbn

    # the Wikipedia citation API is a record endpoint: a missing ISBN is a 404
    monkeypatch.setattr(requests.Session, "get", _fake_response(404))

    assert papis.isbn.meta_wiki("9798104332189") is None


@pytest.mark.parametrize("service", ["goob", "openl"])
def test_meta_not_found_query_endpoint(
        tmp_config: TemporaryConfiguration,
        monkeypatch: pytest.MonkeyPatch,
        service: str) -> None:
    import papis.isbn
    from papis.exceptions import SourceError

    monkeypatch.setattr(requests.Session, "get", _fake_response(404))

    with pytest.raises(SourceError, match="Could not query"):
        papis.isbn.meta("9780486670478", service=service)


def test_json_request_quota_error(tmp_config: TemporaryConfiguration,
                                  monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.isbn
    from papis.exceptions import SourceError

    # NOTE: Google Books reports an exhausted quota with a 429 and a JSON body
    monkeypatch.setattr(
        requests.Session, "get",
        _fake_response(429, b'{"error": {"code": 429}}'))

    with pytest.raises(SourceError, match="Could not query"):
        papis.isbn.json_request("https://example.com")


def test_json_request_invalid_response(
        tmp_config: TemporaryConfiguration,
        monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.isbn
    from papis.exceptions import SourceError

    monkeypatch.setattr(
        requests.Session, "get", _fake_response(200, b"<html>"))

    with pytest.raises(SourceError, match="Unexpected response"):
        papis.isbn.json_request("https://example.com")


def test_get_data_unknown_service(tmp_config: TemporaryConfiguration) -> None:
    import papis.isbn
    from papis.exceptions import SourceError

    with pytest.raises(SourceError, match="Unknown ISBN service"):
        papis.isbn.get_data(isbn_like="9780486670478", service="unknown")


def test_get_data_unexpected_meta_type(
        tmp_config: TemporaryConfiguration,
        monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.isbn
    from papis.exceptions import SourceError

    monkeypatch.setattr(papis.isbn, "meta", lambda *args, **kwargs: "unexpected")

    with pytest.raises(SourceError, match="Unexpected response from ISBN"):
        papis.isbn.get_data(isbn_like="9780486670478")


def test_isbn_from_words_no_match(tmp_config: TemporaryConfiguration,
                                  monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.isbn

    # NOTE: this used to raise an UnboundLocalError instead of reporting
    # that no ISBN could be found
    monkeypatch.setattr(
        requests.Session, "get",
        _fake_response(200, b"<html>no identifiers here</html>"))

    assert papis.isbn.isbn_from_words("some query") is None


def test_isbn_from_words_http_error(tmp_config: TemporaryConfiguration,
                                    monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.isbn
    from papis.exceptions import SourceError

    monkeypatch.setattr(requests.Session, "get", _fake_response(500))

    with pytest.raises(SourceError, match="Could not query"):
        papis.isbn.isbn_from_words("some query")
