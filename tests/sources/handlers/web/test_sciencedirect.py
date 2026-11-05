from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.sources.handlers.web.sciencedirect import ScienceDirectHandler
from tests.sources.helpers import assert_match_cases, lookup_page

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

SCIENCEDIRECT_URLS = (
    "https://www.sciencedirect.com/science/article/abs/pii/S0009261497040141",
    "https://www.sciencedirect.com/science/article/abs/pii/S2210271X18305656",
    "https://www.sciencedirect.com/science/article/pii/S146290112300117X",
)


def test_match() -> None:
    """URLs pointing at the site are matched, others rejected."""
    assert_match_cases(
        ScienceDirectHandler,
        matched=("https://www.sciencedirect.com", *SCIENCEDIRECT_URLS),
        rejected=(
            "https://www.scienceindirect.com",
            "http://www.sciencedirect.co.uk/science/article/pii/S0009261497040141",
        ),
    )


@pytest.mark.parametrize("url", SCIENCEDIRECT_URLS)
def test_lookup(
    tmp_config: TemporaryConfiguration, resource_cache: ResourceCache, url: str
) -> None:
    """Metadata is scraped from the saved page (as content, no network)."""
    uid = url.rsplit("/", 1)[-1]
    result = lookup_page(
        ScienceDirectHandler, resource_cache, f"ScienceDirect_{uid}", url
    )

    assert result.files == []
    assert result.followup is None
