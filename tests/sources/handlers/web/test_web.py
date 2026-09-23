"""Tests for the :class:`WebsiteHandler` base-class defaults."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import papis.crossref
from papis.sources.handler import FileReference, LookupInput
from papis.sources.handlers.web import WebsiteHandler
from tests.sources.helpers import disable_doi_lookup

if TYPE_CHECKING:
    import pytest

    from papis.testing import TemporaryConfiguration


class _MinimalHandler(WebsiteHandler):
    name = "minimal"
    url_or_id_re = re.compile(r".*example\.com.*")


class _DoiHandler(WebsiteHandler):
    name = "minimal-doi"
    url_or_id_re = re.compile(r".*example\.com.*")
    enrich_from_doi = True

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:  # ruff: ignore[no-self-use]
        # NOTE: no scraped data: the DOI comes from get_doi
        return {}

    def get_doi(self, evidence: LookupInput) -> str | None:  # ruff: ignore[no-self-use]
        return "10.1234/example"


class _NoEnrichDoiHandler(_DoiHandler):
    name = "minimal-no-enrich"
    enrich_from_doi = False


class _ScrapedDoiHandler(_DoiHandler):
    name = "minimal-scraped"
    enrich_from_doi = False

    def scrape(self, evidence: LookupInput) -> dict[str, Any]:  # ruff: ignore[no-self-use]
        return {"doi": "10.9999/scraped"}


def test_website_handler_match_ignores_content() -> None:
    """Matching is a URL/ID check: a bare identifier matches even though there is
    nothing to scrape (its metadata may arrive via a followup), while a file is
    not a page to scrape."""
    url = "https://example.com/article"

    assert _MinimalHandler.match_for_lookup(LookupInput(input=url)) is not None
    assert (
        _MinimalHandler.match_for_lookup(
            LookupInput(input=url, kind="webpage", content="<html></html>")
        )
        is not None
    )
    assert (
        _MinimalHandler.match_for_lookup(
            LookupInput(input=url, kind="file", content="<html></html>")
        )
        is None
    )


def test_website_handler_optional_hooks_default(
    tmp_config: TemporaryConfiguration,
) -> None:
    """A handler that overrides nothing looks up to an empty result."""
    evidence = LookupInput(
        input="https://example.com/article",
        kind="webpage",
        content="<html></html>",
    )
    handler = _MinimalHandler.match_for_lookup(evidence)
    assert handler is not None

    assert handler.scrape(evidence) == {}

    result = handler.lookup(evidence)
    assert result.document is None
    assert result.files == []
    assert result.followup is None

    # the optional hooks answer "no" by value, not by raising
    assert handler.get_doi(evidence) is None
    assert handler.get_file_url(evidence) is None
    assert handler.get_bibtex_url(evidence) is None


def test_website_handler_records_url_doi(
    tmp_config: TemporaryConfiguration,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without ``enrich_from_doi`` the DOI is only recorded: the derived
    DOI (``get_doi``) is a field and a DOI scraped by ``parse`` wins over
    it. Neither consults the DOI source."""

    disable_doi_lookup(monkeypatch)

    evidence = LookupInput(
        input="https://example.com/article",
        kind="webpage",
        content="<html></html>",
    )

    handler = _NoEnrichDoiHandler.match_for_lookup(evidence)
    assert handler is not None

    result = handler.lookup(evidence)
    assert result.document == {"doi": "10.1234/example"}
    assert result.files == []
    assert result.followup is None

    handler = _ScrapedDoiHandler.match_for_lookup(evidence)
    assert handler is not None

    result = handler.lookup(evidence)
    assert result.document == {"doi": "10.9999/scraped"}


def test_website_handler_enriches_derived_doi(
    tmp_config: TemporaryConfiguration,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The doi source's metadata is merged under the handler's own data:
    the derived DOI wins, the fetched fields fill the gaps (including the
    document URL that becomes the file reference)."""
    monkeypatch.setattr(
        papis.crossref,
        "doi_to_data",
        lambda doi: {
            "title": "Fetched",
            "doi": doi,
            "doc_url": "https://example.com/paper.pdf",
        },
    )

    evidence = LookupInput(
        input="https://example.com/article",
        kind="webpage",
        content="<html></html>",
    )
    handler = _DoiHandler.match_for_lookup(evidence)
    assert handler is not None

    result = handler.lookup(evidence)
    assert result.document == {
        "doi": "10.1234/example",
        "title": "Fetched",
        "doc_url": "https://example.com/paper.pdf",
    }
    assert result.files == [
        FileReference(extension="pdf", url="https://example.com/paper.pdf")
    ]
    assert result.followup is None
    assert result.message is None


def test_website_handler_doi_enrichment_is_best_effort(
    tmp_config: TemporaryConfiguration,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unknown DOI or a Crossref outage leaves the derived DOI in place
    and reports a caveat instead of failing the scrape."""
    from papis.exceptions import SourceError

    def unknown(doi: str) -> dict[str, Any]:
        raise ValueError("no result")

    def outage(doi: str) -> dict[str, Any]:
        raise SourceError("Crossref is down")

    evidence = LookupInput(
        input="https://example.com/article",
        kind="webpage",
        content="<html></html>",
    )

    for fail in (unknown, outage):
        monkeypatch.setattr(papis.crossref, "doi_to_data", fail)

        handler = _DoiHandler.match_for_lookup(evidence)
        assert handler is not None

        result = handler.lookup(evidence)

        assert result.document == {"doi": "10.1234/example"}
        assert result.files == []
        assert result.followup is None
        assert result.message == (
            "Could not retrieve additional metadata for DOI '10.1234/example'."
        )
