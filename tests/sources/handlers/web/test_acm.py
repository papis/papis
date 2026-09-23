from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import papis.crossref
from papis.sources.handler import FileReference, LookupInput
from papis.sources.handlers.web.acm import ACMHandler
from tests.sources.helpers import assert_match_cases

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration

ACM_URLS = (
    "https://dl.acm.org/doi/10.1145/3833213",
    "https://dl.acm.org/doi/abs/10.1145/3833213",
    "https://dl.acm.org/doi/full/10.1145/3833213",
    "https://dl.acm.org/doi/pdf/10.1145/3833213",
)

ACM_DOI = "10.1145/3833213"
ACM_PDF_URL = f"https://dl.acm.org/doi/pdf/{ACM_DOI}"


def test_match() -> None:
    """URLs pointing at the ACM Digital Library are matched, others
    rejected."""
    assert_match_cases(
        ACMHandler,
        matched=(*ACM_URLS,),
        rejected=("https://acm.co.uk/doi/10.1145/3544548.3583159",),
    )


@pytest.mark.parametrize("url", ACM_URLS)
def test_lookup(
    tmp_config: TemporaryConfiguration, monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    """The DOI in the URL keys the PDF link and is enriched with the doi
    source's metadata by the base class, so the handler contributes
    metadata without any scrape of its own."""
    monkeypatch.setattr(
        papis.crossref, "doi_to_data", lambda doi: {"title": "A paper", "doi": doi}
    )

    evidence = LookupInput(input=url, kind="webpage", content="<html></html>")
    handler = ACMHandler.match_for_lookup(evidence)
    assert handler is not None

    result = handler.lookup(evidence)
    assert result.document == {"doi": ACM_DOI, "title": "A paper"}
    assert result.followup is None
    assert result.files == [FileReference(extension="pdf", url=ACM_PDF_URL)]
