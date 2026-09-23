from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.sources.handler import FileReference
from papis.sources.handlers.web.springer import SpringerHandler
from tests.sources.helpers import (
    assert_bibtex_followup,
    assert_match_cases,
    lookup_page,
)

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

SPRINGER_URLS = (
    "https://link.springer.com/article/10.1007/s10924-010-0192-1",
    "https://link.springer.com/article/10.1007/BF02727953",
)


def test_match() -> None:
    """URLs pointing at the site are matched, others rejected."""
    assert_match_cases(
        SpringerHandler,
        matched=("https://link.springer.com", *SPRINGER_URLS),
        rejected=(
            "https://links.springer.com/article/123",
            "https://link.springer.co.uk/article/123",
        ),
    )


@pytest.mark.parametrize("url", SPRINGER_URLS)
def test_lookup(
    tmp_config: TemporaryConfiguration, resource_cache: ResourceCache, url: str
) -> None:
    """Metadata is scraped from the saved page (as content, no network)."""
    uid = url.rsplit("/", 1)[-1].replace("-", "_")
    doi = url.split("/article/")[1]
    result = lookup_page(SpringerHandler, resource_cache, f"SpringerLink_{uid}", url)

    assert result.files == [
        FileReference(
            url=f"https://link.springer.com/content/pdf/{doi}.pdf", extension="pdf"
        )
    ]
    assert_bibtex_followup(
        result,
        (
            "https://citation-needed.springer.com/v2/references/"
            f"{doi}?format=bibtex&flavour=citation"
        ),
    )
