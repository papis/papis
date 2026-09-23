from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.sources.handler import FileReference, LookupInput
from papis.sources.handlers.web.taylorandfrancis import TaylorAndFrancisHandler
from tests.sources.helpers import (
    assert_bibtex_followup,
    assert_match_cases,
    lookup_page,
)

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

TAYLORANDFRANCIS_URLS = (
    "https://www.tandfonline.com/doi/full/10.1080/00268976.2013.788745",
    "https://www.tandfonline.com/doi/full/10.1080/23311932.2015.1117749",
)


def test_match() -> None:
    """URLs pointing at the site are matched, others rejected."""
    assert_match_cases(
        TaylorAndFrancisHandler,
        matched=("https://tandfonline.com", *TAYLORANDFRANCIS_URLS),
        rejected=(
            "https://torfonline.com/article/123",
            "https://tandfonline.co.uk/article/123",
        ),
    )


@pytest.mark.parametrize("url", TAYLORANDFRANCIS_URLS)
def test_lookup(
    tmp_config: TemporaryConfiguration, resource_cache: ResourceCache, url: str
) -> None:
    """Metadata is scraped from the saved page (as content, no network)."""
    uid = url.rsplit("/", 1)[-1]
    doi = url.split("/doi/full/")[1]
    result = lookup_page(
        TaylorAndFrancisHandler, resource_cache, f"TaylorAndFrancis_{uid}", url
    )

    assert result.files == [
        FileReference(url=f"https://www.tandfonline.com/doi/pdf/{doi}", extension="pdf")
    ]
    assert_bibtex_followup(
        result,
        (
            "https://www.tandfonline.com/action/downloadCitation"
            f"?doi={doi}&format=bibtex"
        ),
    )


@pytest.mark.parametrize(
    ("url", "doi"),
    [
        (
            "https://www.tandfonline.com/doi/full/10.1080/00268976.2013.788745",
            "10.1080/00268976.2013.788745",
        ),
        (
            "https://www.tandfonline.com/doi/abs/10.1080/00268976.2013.788745",
            "10.1080/00268976.2013.788745",
        ),
        (
            "https://www.tandfonline.com/doi/pdf/10.1080/00268976.2013.788745",
            "10.1080/00268976.2013.788745",
        ),
        # the query and fragment are not part of the DOI
        (
            "https://www.tandfonline.com/doi/full/10.1080/00268976.2013.788745"
            "?needAccess=true&journalCode=tmph20#abstract",
            "10.1080/00268976.2013.788745",
        ),
    ],
)
def test_doi_from_url(
    tmp_config: TemporaryConfiguration, url: str, doi: str
) -> None:
    """A page without a DOI meta tag (even one without any metadata, e.g. a
    bot block) still yields its DOI, taken from the URL."""
    evidence = LookupInput(input=url, kind="webpage", content="<html></html>")
    handler = TaylorAndFrancisHandler.match_for_lookup(evidence)
    assert handler is not None

    result = handler.lookup(evidence)
    assert (result.document or {})["doi"] == doi
