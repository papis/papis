from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
import requests

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration, TemporaryLibrary


@pytest.mark.resource_setup(cachedir="resources/zenodo")
@pytest.mark.parametrize("markdownify", [True, False])
@pytest.mark.parametrize("zenodo_id", ["7391177", "10794563"])
def test_zenodo_id_to_data(tmp_library: TemporaryLibrary,
                           resource_cache: ResourceCache,
                           monkeypatch: pytest.MonkeyPatch,
                           markdownify: bool,
                           zenodo_id: str) -> None:
    import papis.zenodo

    if markdownify:
        pytest.importorskip("markdownify")
        v = "_"
    else:
        v = "_html_"
        monkeypatch.setattr(
            papis.zenodo, "_get_text_from_html",
            lambda html: html)

    infile = f"{zenodo_id}.json"
    outfile = f"{zenodo_id}{v}out.json"

    monkeypatch.setattr(
        papis.zenodo, "_get_zenodo_response",
        lambda zid: resource_cache.get_remote_resource(
            infile, papis.zenodo.ZENODO_URL.format(record_id=zid)
            ).decode()
    )

    input_data = papis.zenodo.get_data(zenodo_id)
    actual_data = papis.zenodo.zenodo_data_to_papis_data(input_data)
    expected_data = resource_cache.get_local_resource(outfile, actual_data)

    assert expected_data == actual_data


def _fake_response(status_code: int = 200, content: bytes = b"") -> Any:
    """Return a replacement for ``requests.Session.get``."""
    def get(self: Any, url: str, **kwargs: Any) -> requests.Response:
        response = requests.Response()
        response.url = url
        response.status_code = status_code
        response._content = content
        return response

    return get


def test_get_data_missing_record(tmp_config: TemporaryConfiguration,
                                 monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.zenodo

    monkeypatch.setattr(
        requests.Session, "get",
        _fake_response(404, b'{"status": 404, "message": "Not found."}'))

    assert papis.zenodo.get_data("7391177") == {}


def test_get_data_http_error(tmp_config: TemporaryConfiguration,
                             monkeypatch: pytest.MonkeyPatch) -> None:
    import papis.zenodo
    from papis.exceptions import SourceError

    monkeypatch.setattr(requests.Session, "get", _fake_response(500))

    with pytest.raises(SourceError, match="Could not query Zenodo"):
        papis.zenodo.get_data("7391177")


@pytest.mark.parametrize("content", [b"<html>", b"[1, 2, 3]"])
def test_get_data_invalid_response(tmp_config: TemporaryConfiguration,
                                   monkeypatch: pytest.MonkeyPatch,
                                   content: bytes) -> None:
    import papis.zenodo
    from papis.exceptions import SourceError

    monkeypatch.setattr(requests.Session, "get", _fake_response(200, content))

    with pytest.raises(SourceError, match="Unexpected response from Zenodo"):
        papis.zenodo.get_data("7391177")
