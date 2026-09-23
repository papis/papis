from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.sources.handlers.web.lingbuzz import LingbuzzHandler
from tests.sources.helpers import assert_match_cases, lookup_page

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

LINGBUZZ_URLS = (
    "https://ling.auf.net/lingbuzz/006747",
    "https://lingbuzz.net/lingbuzz/008324",
)


def test_match() -> None:
    """URLs pointing at the site are matched, others rejected."""
    assert_match_cases(
        LingbuzzHandler,
        matched=(
            "https://lingbuzz.net/000002",
            "https://ling.auf.net/lingbuzz/2",
            *LINGBUZZ_URLS,
        ),
        rejected=("https://lingbuzz.co.uk/000002", "https://arxiv.org/abs/1000.00001"),
    )


@pytest.mark.parametrize("url", LINGBUZZ_URLS)
def test_lookup(
    tmp_config: TemporaryConfiguration, resource_cache: ResourceCache, url: str
) -> None:
    """Metadata is scraped from the saved page (as content, no network); a
    DOI in the "Published in" note is recorded without consulting the DOI
    source (see the website base-class tests)."""
    uid = url.rsplit("/", 1)[-1]
    result = lookup_page(LingbuzzHandler, resource_cache, f"Lingbuzz_{uid}", url)

    assert result.files
    assert result.followup is None
