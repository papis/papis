from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.sources.handler import FileReference
from papis.sources.handlers.web.acl import ACLHandler
from tests.sources.helpers import (
    assert_bibtex_followup,
    assert_match_cases,
    lookup_page,
)

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

ACL_URLS = (
    "https://aclanthology.org/N04-1001",
    "https://aclanthology.org/2021.naacl-main.208",
)


def test_match() -> None:
    """URLs pointing at the site are matched, others rejected."""
    assert_match_cases(
        ACLHandler,
        matched=("https://aclanthology.org", *ACL_URLS),
        rejected=(
            "https://aclanthology.co.uk/article/123",
            "https://abs.org/article/123",
        ),
    )


@pytest.mark.parametrize("url", ACL_URLS)
def test_lookup(
    tmp_config: TemporaryConfiguration, resource_cache: ResourceCache, url: str
) -> None:
    """Metadata is scraped from the saved page (as content, no network)."""
    uid = url.rsplit("/", 1)[-1]
    result = lookup_page(ACLHandler, resource_cache, f"ACL_{uid}", url)

    assert result.files == [FileReference(url=f"{url}.pdf", extension="pdf")]
    assert_bibtex_followup(result, f"{url}.bib")
