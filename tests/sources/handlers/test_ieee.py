from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import papis.utils
from papis.sources.handler import FileReference, LookupInput
from papis.sources.handlers.ieee import IEEEHandler
from tests.sources.helpers import FakeSession

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

IEEE_URLS = (
    "https://ieeexplore.ieee.org/document/12345678",
    "ieee:12345678",
    "https://ieeexplore.ieee.org/document/12345678.pdf",
)

#: Real IEEE Xplore documents whose BibTeX exports are cached as resources.
IEEE_ARNUMBERS = ("9728473", "11062661")

#: the endpoint the handler fetches the export from
BIBTEX_URL = "https://ieeexplore.ieee.org/rest/search/citation/format"


@pytest.mark.parametrize(
    ("input_str", "expected_identifier"),
    [
        ("https://ieeexplore.ieee.org/document/12345678", "12345678"),
        ("ieee:12345678", "12345678"),
        ("https://ieeexplore.ieee.org/document/12345678.pdf", "12345678"),
        ("https://ieeexplore.ieee.org/document/12345678/", "12345678"),
        # URLs without a document identifier, batch identifiers and
        # non-numeric identifiers are not claims
        ("https://example.com/document/12345678", None),
        ("ieee:", None),
        ("ieee:   ", None),
        ("ieee:9728473,11062661", None),
        ("ieee:notanumber", None),
        # URL forms without a single numeric document identifier
        ("https://ieeexplore.ieee.org/document/", None),
        ("https://ieeexplore.ieee.org/document", None),
        ("https://ieeexplore.ieee.org/document/9728473,11062661", None),
        ("https://ieeexplore.ieee.org/document/notanumber", None),
    ],
)
def test_match(input_str: str, expected_identifier: str | None) -> None:
    instance = IEEEHandler.match_for_lookup(LookupInput(input=input_str))
    if expected_identifier is None:
        assert instance is None
    else:
        assert instance is not None
        assert instance.identifier == expected_identifier


@pytest.mark.parametrize("arnumber", IEEE_ARNUMBERS)
def test_lookup(
    tmp_config: TemporaryConfiguration,
    monkeypatch: pytest.MonkeyPatch,
    resource_cache: ResourceCache,
    arnumber: str,
) -> None:
    """The BibTeX export is fetched with the endpoint's query parameters
    and parsed into the document."""
    from papis.bibtex import _bibtexparser_version  # ruff: ignore[import-private-name]

    if _bibtexparser_version() == "v1":
        pytest.skip("bibtexparser v1 keeps months as strings")

    url = f"https://ieeexplore.ieee.org/document/{arnumber}"
    evidence = LookupInput(input=url)
    handler = IEEEHandler.match_for_lookup(evidence)
    assert handler is not None

    export_params = {
        "recordIds": arnumber,
        "citations-format": "citation-abstract",
        "download-format": "download-bibtex",
    }
    export_headers = {"Referer": url}

    #: the real export, cached as a resource (regenerable via
    #: ``PAPIS_UPDATE_RESOURCES=remote``)
    content = resource_cache.get_remote_resource(
        f"IEEE_{arnumber}.json",
        BIBTEX_URL,
        params=export_params,
        headers=export_headers,
    )
    session = FakeSession(content)
    monkeypatch.setattr(papis.utils, "get_session", lambda: session)

    result = handler.lookup(evidence)

    #: metadata comes from the JSON-wrapped BibTeX
    assert result.document is not None
    expected = resource_cache.get_local_resource(
        f"IEEE_{arnumber}_Out.json", result.document
    )
    assert result.document == expected

    #: the PDF link is derived from the document identifier
    assert result.files == [
        FileReference(
            extension="pdf",
            url="https://ieeexplore.ieee.org/stampPDF/getPDF.jsp"
            f"?tp=&isnumber=&arnumber={arnumber}",
        )
    ]
    assert result.followup is None


@pytest.mark.parametrize(
    ("status_code", "content"),
    [
        #: 404/410 do not signal absence for this endpoint: they are errors
        (404, b""),
        (410, b""),
        (500, b"<html>server error</html>"),
        (200, b"<html>blocked</html>"),
        (200, b"{}"),
    ],
)
def test_lookup_failure(
    tmp_config: TemporaryConfiguration,
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
    content: bytes,
) -> None:
    """Unrecognized HTTP failures and malformed exports are errors, not absence."""
    from papis.exceptions import SourceError

    url = "https://ieeexplore.ieee.org/document/12345678"
    handler = IEEEHandler.match_for_lookup(LookupInput(input=url))
    assert handler is not None

    session = FakeSession(content, status_code=status_code)
    monkeypatch.setattr(papis.utils, "get_session", lambda: session)

    with pytest.raises(SourceError, match="IEEE"):
        handler.lookup(LookupInput(input=url))


@pytest.mark.parametrize(
    ("status_code", "content"),
    [
        #: IEEE reports a nonexistent record as 500 + ``{"reason": "Unknown"}``
        (500, b'{"reason": "Unknown"}'),
        #: an empty export means the same thing
        (200, b'{"data": "\\r\\n"}'),
    ],
)
def test_lookup_not_found(
    tmp_config: TemporaryConfiguration,
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
    content: bytes,
) -> None:
    """A missing record is absence (empty result), despite the HTTP status."""
    url = "https://ieeexplore.ieee.org/document/12345678"
    handler = IEEEHandler.match_for_lookup(LookupInput(input=url))
    assert handler is not None

    session = FakeSession(content, status_code=status_code)
    monkeypatch.setattr(papis.utils, "get_session", lambda: session)

    result = handler.lookup(LookupInput(input=url))
    assert result.document is None
    assert result.files == []
