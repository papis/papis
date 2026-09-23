from __future__ import annotations

from typing import TYPE_CHECKING

from papis.sources.handler import FileReference, LookupInput
from papis.sources.handlers.web.thesesfr import ThesesFrHandler
from tests.sources.helpers import assert_bibtex_followup, assert_match_cases

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration


def test_match() -> None:
    """URLs pointing at theses.fr are matched, others rejected."""
    assert_match_cases(
        ThesesFrHandler,
        matched=(
            "https://www.theses.fr/2014TOU30305",
            "https://www.theses.fr/2014TOU30305.bib/?asdf=2",
        ),
        rejected=("http://google.com", "2014TOU", "ASDF"),
    )

    # a bare thesis identifier names a page: there is nothing to scrape, but
    # the identifier is enough to ask for the BibTeX export
    handler = ThesesFrHandler.match_for_lookup(LookupInput(input="2014TOU30305"))
    assert handler is not None

    result = handler.lookup(LookupInput(input="2014TOU30305"))
    assert result.document is None
    assert_bibtex_followup(result, "https://www.theses.fr/2014TOU30305.bib")


def test_lookup(tmp_config: TemporaryConfiguration) -> None:
    """The BibTeX export followup carries the document, the document link is
    derived from the thesis identifier in the URL."""
    url = "https://theses.fr/2014TOU30305"
    evidence = LookupInput(input=url, kind="webpage", content="<html></html>")
    handler = ThesesFrHandler.match_for_lookup(evidence)
    assert handler is not None

    result = handler.lookup(evidence)

    # no scraped data: the document arrives as the completed followup,
    # the document reference on the result itself
    assert result.document is None
    assert result.files == [
        FileReference(
            extension="pdf", url="https://theses.fr/api/v1/document/2014TOU30305"
        )
    ]
    assert_bibtex_followup(result, "https://www.theses.fr/2014TOU30305.bib")
