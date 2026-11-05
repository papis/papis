from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.sources.handlers.web.aps import APSHandler
from tests.sources.helpers import (
    assert_bibtex_followup,
    assert_match_cases,
    lookup_page,
)

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

APS_URLS = (
    "https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.122.145901",
    "https://journals.aps.org/prx/abstract/10.1103/PhysRevX.12.041027",
    "https://journals.aps.org/rmp/abstract/10.1103/RevModPhys.94.045004",
)


def test_match() -> None:
    """URLs pointing at the site are matched, others rejected."""
    assert_match_cases(
        APSHandler,
        matched=("https://aps.org", *APS_URLS),
        rejected=("https://aps.co.uk/article/123",),
    )


@pytest.mark.parametrize("url", APS_URLS)
def test_lookup(
    tmp_config: TemporaryConfiguration, resource_cache: ResourceCache, url: str
) -> None:
    """Metadata is scraped from the saved page (as content, no network)."""
    uid = url.rsplit("/", 1)[-1]
    result = lookup_page(APSHandler, resource_cache, f"APS_{uid}", url)

    assert result.files
    assert result.followup is not None
    journal = url.split("/")[3]
    doi = url.split("/abstract/")[1]
    assert_bibtex_followup(
        result,
        f"https://journals.aps.org/{journal}/export/{doi}?type=bibtex&download=true",
    )
