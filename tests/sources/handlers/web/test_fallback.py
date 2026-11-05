from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.sources.handler import LookupInput
from papis.sources.handlers.web import FallbackHandler
from tests.sources.helpers import assert_match_cases, lookup_page

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

FALLBACK_URLS = (
    "https://peerj.com/articles/4886/",
    # NOTE: the old docId/481 URL is dead; this frontdoor still works
    "https://opus4.kobv.de/opus4-trr154/frontdoor/index/index/start/0/"
    "rows/10/sortfield/score/sortorder/desc/searchtype/simple/query/trr154/"
    "docId/200",
)


def test_match() -> None:
    """The fallback handler claims any URL-shaped input."""
    assert_match_cases(
        FallbackHandler,
        matched=(*FALLBACK_URLS, "https://random-website.com/whatever"),
        rejected=("", "10.1103/PhysRevLett.122.145901", "not a url"),
    )


def test_lookup_title(tmp_config: TemporaryConfiguration) -> None:
    """The page ``<title>`` is read from the element text, not from a
    ``content`` attribute (which used to yield the string ``'None'``)."""
    evidence = LookupInput(
        input="https://duckduckgo.com/?q=pyreverse",
        kind="webpage",
        content=(
            "<html><head><title> pyreverse at DuckDuckGo </title>"
            '<meta name="description" content="DuckDuckGo. Privacy, Simplified.">'
            "</head><body></body></html>"
        ),
    )
    handler = FallbackHandler.match_for_lookup(evidence)
    assert handler is not None

    result = handler.lookup(evidence)
    assert result.document is not None
    assert result.document["title"] == "pyreverse at DuckDuckGo"


@pytest.mark.parametrize("url", FALLBACK_URLS)
def test_lookup(
    tmp_config: TemporaryConfiguration, resource_cache: ResourceCache, url: str
) -> None:
    """Metadata is scraped from the saved page (as content, no network)."""
    from urllib.parse import urlparse

    uid = urlparse(url).netloc.split(".")[-2]
    result = lookup_page(FallbackHandler, resource_cache, f"Fallback_{uid}", url)

    # no bibtex export followups for the fallback
    assert result.followup is None
    assert result.document is not None
    if result.document.get("doc_url"):
        assert result.files[0].url == result.document["doc_url"]
        # the fallback accepts any type (no expected extension)
        assert result.files[0].extension is None
    else:
        assert result.files == []
