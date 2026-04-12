from __future__ import annotations

import os
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from papis.document import Document
    from papis.testing import TemporaryConfiguration


def get_docs() -> list[Document]:
    from papis.document import from_data

    yamlfile = os.path.join(os.path.dirname(__file__), "data", "licl.yaml")
    with open(yamlfile, encoding="utf-8") as f:
        return [from_data(data) for data in yaml.safe_load_all(f)]


def test_docmatcher(tmp_config: TemporaryConfiguration) -> None:
    from papis.docmatcher import DocumentMatcher, make_document_matcher

    matcher = make_document_matcher("author:einstein")
    assert isinstance(matcher, DocumentMatcher)
    assert matcher.search == "author:einstein"
    assert matcher.query is not None

    docs = get_docs()
    assert len(list(docs)) == 16

    # Test basic term matching (case-insensitive)
    matcher = make_document_matcher("Lithium")
    assert any(matcher(doc) for doc in docs)
    assert all(not matcher(doc) for doc in docs
               if "Lithium" not in doc.get("title", ""))

    # Test key:value matching
    matcher = make_document_matcher("author:Seitz")
    matched_docs = [doc for doc in docs if matcher(doc)]
    assert len(matched_docs) > 0
    assert all("Seitz" in doc.get("author", "") for doc in matched_docs)

    # Test multiple terms (AND logic)
    matcher = make_document_matcher("Lithium author:Iwata")
    matched_docs = [doc for doc in docs if matcher(doc)]
    assert len(matched_docs) == 1
    assert "Lithium" in matched_docs[0].get("title", "")
    assert "Iwata" in matched_docs[0].get("author", "")

    # Test quoted strings with spaces
    matcher = make_document_matcher('title:"Lithium Chloride"')
    matched_docs = [doc for doc in docs if matcher(doc)]
    assert len(matched_docs) > 0
    assert all("Lithium Chloride" in doc.get("title", "") for doc in matched_docs)

    # Test non-existent key (should not match)
    matcher = make_document_matcher("nonexistentkey:value")
    assert all(not matcher(doc) for doc in docs)

    # Test non-matching term
    matcher = make_document_matcher("thistermshouldnotexistanywhere")
    assert all(not matcher(doc) for doc in docs)

    # Test regex characters in query
    matcher = make_document_matcher("year:200[0-9]")
    matched_docs = [doc for doc in docs if matcher(doc)]
    assert all(2000 <= int(doc.get("year", 0)) <= 2009 for doc in matched_docs)


def test_parse_query(tmp_config: TemporaryConfiguration) -> None:
    from papis.docmatcher import Pair, Term, parse_query

    rs = parse_query("hello   author : einstein")
    assert len(rs.children) == 2

    child = rs.children[0]
    assert isinstance(child, Term)
    assert child.query == "hello"

    child = rs.children[1]
    assert isinstance(child, Pair)
    assert child.key == "author"
    assert child.query == "einstein"

    rs = parse_query("doi : 123.123/124_123")
    assert len(rs.children) == 1

    child = rs.children[0]
    assert isinstance(child, Pair)
    assert child.key == "doi"
    assert child.query == "123.123/124_123"

    rs = parse_query("doi : 123.123/124_123(80)12")
    assert len(rs.children) == 1

    child = rs.children[0]
    assert isinstance(child, Pair)
    assert child.key == "doi"
    assert child.query == "123.123/124_123(80)12"

    rs = parse_query('tt : asfd   author : "Albert einstein"')
    assert len(rs.children) == 2

    child = rs.children[0]
    assert isinstance(child, Pair)
    assert child.key == "tt"
    assert child.query == "asfd"

    child = rs.children[1]
    assert isinstance(child, Pair)
    assert child.key == "author"
    assert child.query == '"Albert einstein"'


def test_parse_query_unicode(tmp_config: TemporaryConfiguration) -> None:
    from papis.docmatcher import Pair, Term, parse_query

    # Test Unicode in Terms
    rs = parse_query("πρέπεις 123")
    assert len(rs.children) == 2
    assert isinstance(rs.children[0], Term)
    assert rs.children[0].query == "πρέπεις"
    assert isinstance(rs.children[1], Term)
    assert rs.children[1].query == "123"

    # Test Unicode in Keys and Values
    rs = parse_query("συγγραφέας : 'Αλβέρτος Αϊνστάιν'")
    assert len(rs.children) == 1
    child = rs.children[0]
    assert isinstance(child, Pair)
    assert child.key == "συγγραφέας"
    assert child.query == "'Αλβέρτος Αϊνστάιν'"

    # Test Unicode in Quoted Terms
    rs = parse_query('"你好世界" tags : "中文"')
    assert len(rs.children) == 2
    assert isinstance(rs.children[0], Term)
    assert rs.children[0].query == '"你好世界"'
    assert isinstance(rs.children[1], Pair)
    assert rs.children[1].key == "tags"
    assert rs.children[1].query == '"中文"'


def test_docmatcher_config_format(tmp_config: TemporaryConfiguration) -> None:
    import papis.config
    from papis.docmatcher import make_document_matcher
    from papis.document import from_data

    doc = from_data({"title": "Physics Paper", "custom_field": "HiddenValue"})

    # Case 1: Default format only includes title
    # Should not match because "HiddenValue" is not in the formatted title
    papis.config.set("match-format", "{doc[title]}")
    matcher = make_document_matcher("HiddenValue")
    assert not matcher(doc)

    # Case 2: Update format to include the custom field
    # Re-create matcher to pick up new config default
    papis.config.set("match-format", "{doc[title]} {doc[custom_field]}")
    matcher = make_document_matcher("HiddenValue")
    assert matcher(doc)

    # Case 3: Pass explicit format to make_document_matcher
    matcher = make_document_matcher("HiddenValue", match_format="{doc[title]}")
    assert not matcher(doc)
