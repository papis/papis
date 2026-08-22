from __future__ import annotations

import os
from typing import TYPE_CHECKING

import papis.citations
from papis.document import Document

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration


def test_save_and_get_citations(tmp_config: TemporaryConfiguration) -> None:
    """Test that saving and retrieving citations is a roundtrip."""
    doc = Document(
        folder=tmp_config.libdir,
        data={"title": "Test Doc", "doi": "10.1000/test"},
    )
    citations = [{"title": "Cited 1", "doi": "10.1000/cited1"}]
    papis.citations.save_citations(doc, citations)

    assert papis.citations.has_citations(doc)
    result = papis.citations.get_citations(doc)
    assert result == citations


def test_get_citations_empty(tmp_config: TemporaryConfiguration) -> None:
    """get_citations returns [] when there is no citations file."""
    doc = Document(
        folder=tmp_config.libdir,
        data={"title": "Test Doc", "doi": "10.1000/test"},
    )
    assert papis.citations.get_citations(doc) == []
    assert not papis.citations.has_citations(doc)


def test_save_and_get_cited_by(tmp_config: TemporaryConfiguration) -> None:
    """Test that saving and retrieving cited-by data is a roundtrip."""
    doc = Document(
        folder=tmp_config.libdir,
        data={"title": "Test Doc", "doi": "10.1000/test"},
    )
    cited_by = [{"title": "Cites me 1", "doi": "10.1000/citesme1"}]
    papis.citations.save_cited_by(doc, cited_by)

    assert papis.citations.has_cited_by(doc)
    result = papis.citations.get_cited_by(doc)
    assert result == cited_by


def test_get_cited_by_empty(tmp_config: TemporaryConfiguration) -> None:
    """get_cited_by returns [] when there is no cited-by file."""
    doc = Document(
        folder=tmp_config.libdir,
        data={"title": "Test Doc", "doi": "10.1000/test"},
    )
    assert papis.citations.get_cited_by(doc) == []
    assert not papis.citations.has_cited_by(doc)


def test_save_cited_by_creates_cited_by_file(
    tmp_config: TemporaryConfiguration,
) -> None:
    """save_cited_by creates a cited-by.yaml file."""
    doc = Document(
        folder=tmp_config.libdir,
        data={"title": "Test Doc", "doi": "10.1000/test"},
    )
    papis.citations.save_cited_by(
        doc, [{"title": "Cites me", "doi": "10.1000/citesme"}]
    )

    cited_by_file = papis.citations.get_cited_by_file(doc)
    assert cited_by_file is not None
    assert os.path.exists(cited_by_file)
    assert os.path.basename(cited_by_file) == "cited-by.yaml"


def test_save_citations_creates_citations_file(
    tmp_config: TemporaryConfiguration,
) -> None:
    """save_citations creates a citations.yaml file."""
    doc = Document(
        folder=tmp_config.libdir,
        data={"title": "Test Doc", "doi": "10.1000/test"},
    )
    papis.citations.save_citations(
        doc, [{"title": "Cites me", "doi": "10.1000/citesme"}]
    )

    citations_file = papis.citations.get_citations_file(doc)
    assert citations_file is not None
    assert os.path.exists(citations_file)
    assert os.path.basename(citations_file) == "citations.yaml"


def test_get_metadata_citations_filters_non_doi() -> None:
    doc = Document(
        data={
            "title": "Test",
            "citations": [
                {"title": "With DOI", "doi": "10.1000/1"},
                {"title": "No DOI"},
                "not a dict",
            ],
        }
    )
    result = papis.citations.get_metadata_citations(doc)

    assert len(result) == 1
    assert result[0]["doi"] == "10.1000/1"
