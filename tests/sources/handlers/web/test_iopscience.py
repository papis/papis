from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from papis.sources.handler import FileReference, LookupInput
from papis.sources.handlers.web.iopscience import IOPscienceHandler
from tests.sources.helpers import (
    assert_bibtex_followup,
    assert_match_cases,
    assert_no_contribution,
    lookup_page,
)

if TYPE_CHECKING:
    from papis.testing import ResourceCache, TemporaryConfiguration

IOPSCIENCE_URLS = (
    "https://iopscience.iop.org/article/10.1088/0026-1394/12/4/002",
    "https://iopscience.iop.org/article/10.1088/1748-605X/ab007b",
)


def test_match() -> None:
    """URLs pointing at the site are matched, others rejected."""
    assert_match_cases(
        IOPscienceHandler,
        matched=(
            "https://iopscience.iop.org",
            "https://iopscience.iop.org/article/10.1088/0026-1394/12/4/002/pdf",
            *IOPSCIENCE_URLS,
        ),
        rejected=(
            "https://iop.org/article/123",
            "https://iopscience.iop.co.uk/article/123",
        ),
    )


def test_lookup_no_doi(tmp_config: TemporaryConfiguration) -> None:
    """A matched iopscience URL without a DOI contributes nothing (the
    legacy prefix slice would have produced the path tail as a DOI)."""
    evidence = LookupInput(
        input="https://iopscience.iop.org/journal/1742-6596",
        kind="webpage",
        content="<html></html>",
    )
    handler = IOPscienceHandler.match_for_lookup(evidence)
    assert handler is not None

    result = handler.lookup(evidence)
    assert_no_contribution(result)


@pytest.mark.parametrize("url", IOPSCIENCE_URLS)
def test_lookup(
    tmp_config: TemporaryConfiguration, resource_cache: ResourceCache, url: str
) -> None:
    """Metadata is scraped from the saved page (as content, no network)."""
    uid = url.rsplit("/", 1)[-1]
    doi = url.split("/article/")[1]
    result = lookup_page(IOPscienceHandler, resource_cache, f"IOPScience_{uid}", url)

    assert result.files == [
        FileReference(
            url=f"https://iopscience.iop.org/article/{doi}/pdf", extension="pdf"
        )
    ]
    assert_bibtex_followup(
        result,
        (
            "https://iopscience.iop.org/export?type=article"
            f"&doi={doi}&exportFormat=iopexport_bib&exportType=abs"
            "&navsubmit=Export+abstract"
        ),
    )
