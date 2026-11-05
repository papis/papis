from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.sources.handler import FileReference, LookupInput
from papis.sources.handlers.web.frontiersin import FrontiersInHandler
from tests.sources.helpers import (
    assert_bibtex_followup,
    assert_match_cases,
    assert_no_contribution,
    disable_doi_lookup,
)

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

FRONTIERSIN_URLS = (
    (
        "https://www.frontiersin.org/articles/10.3389/fnins.2023.1123456/full",
        "10.3389/fnins.2023.1123456",
    ),
    (
        "https://www.frontiersin.org/articles/10.3389/fnins.2023.1123456/pdf",
        "10.3389/fnins.2023.1123456",
    ),
    (
        "https://www.frontiersin.org/journals/psychology/articles/"
        "10.3389/fpsyg.2024.1234567/full",
        "10.3389/fpsyg.2024.1234567",
    ),
)

#: real Frontiers article whose page is saved as a resource
FRONTIERSIN_MICROBIOLOGY_URL = (
    "https://www.frontiersin.org/journals/microbiology/articles/"
    "10.3389/fmicb.2023.1326870/full"
)
FRONTIERSIN_MICROBIOLOGY_DOI = "10.3389/fmicb.2023.1326870"


def test_match() -> None:
    """URLs pointing at Frontiers are matched, others rejected."""
    assert_match_cases(
        FrontiersInHandler,
        matched=("https://www.frontiersin.org", *(url for url, _ in FRONTIERSIN_URLS)),
        rejected=(
            "https://frontiersin.co.uk/articles/10.3389/fnins.2023.1123456/full",
        ),
    )


def test_lookup_non_doi_path(tmp_config: TemporaryConfiguration) -> None:
    """An article path without a DOI yields nothing (the legacy regex
    accepted any two path segments as a DOI)."""
    evidence = LookupInput(
        input="https://www.frontiersin.org/articles/foo/bar/full",
        kind="webpage",
        content="<html></html>",
    )

    handler = FrontiersInHandler.match_for_lookup(evidence)
    assert handler is not None

    result = handler.lookup(evidence)
    assert_no_contribution(result)


@pytest.mark.parametrize(("url", "expected_doi"), FRONTIERSIN_URLS)
def test_lookup(
    tmp_config: TemporaryConfiguration,
    monkeypatch: pytest.MonkeyPatch,
    url: str,
    expected_doi: str,
) -> None:
    """The DOI is parsed from the URL (the site's ``/full`` and ``/pdf``
    suffixes are not swallowed by the basic pattern) and the PDF link
    derived from it; the DOI is recorded without consulting the DOI source,
    and the dummy page has no export link, so there is no BibTeX followup."""
    disable_doi_lookup(monkeypatch)
    evidence = LookupInput(input=url, kind="webpage", content="<html></html>")
    handler = FrontiersInHandler.match_for_lookup(evidence)
    assert handler is not None

    result = handler.lookup(evidence)
    assert result.document == {"doi": expected_doi}
    assert result.followup is None
    assert result.files == [
        FileReference(
            extension="pdf",
            url=f"https://www.frontiersin.org/articles/{expected_doi}/pdf",
        )
    ]


def test_lookup_saved_page(
    tmp_config: TemporaryConfiguration,
    monkeypatch: pytest.MonkeyPatch,
    resource_cache: ResourceCache,
) -> None:
    """The saved page's meta headers populate the document (so the DOI
    source is not consulted) and its BibTeX link yields the followup."""
    disable_doi_lookup(monkeypatch)
    content = resource_cache.get_remote_resource(
        "Frontiersin_10.3389_fmicb.2023.1326870.html", FRONTIERSIN_MICROBIOLOGY_URL
    ).decode()
    evidence = LookupInput(
        input=FRONTIERSIN_MICROBIOLOGY_URL,
        kind="webpage",
        content=content,
    )

    handler = FrontiersInHandler.match_for_lookup(evidence)
    assert handler is not None
    result = handler.lookup(evidence)

    assert result.document is not None
    assert result.document["doi"] == FRONTIERSIN_MICROBIOLOGY_DOI
    assert result.document["title"] == (
        "Alteration of the gut microbiota profile in children with autism "
        "spectrum disorder in China"
    )

    assert_bibtex_followup(
        result,
        (
            "https://public-pages-files-2025.frontiersin.org/journals/"
            f"microbiology/articles/{FRONTIERSIN_MICROBIOLOGY_DOI}/bibTex"
        ),
    )
