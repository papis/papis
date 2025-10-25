from __future__ import annotations

import os
from functools import partial
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    import re

    from papis.document import Document
    from papis.testing import TemporaryConfiguration


def get_docs() -> list[Document]:
    from papis.document import from_data

    yamlfile = os.path.join(os.path.dirname(__file__), "data", "licl.yaml")
    with open(yamlfile, encoding="utf-8") as f:
        return [from_data(data) for data in yaml.safe_load_all(f)]


def docmatcher_matcher(
        res: tuple[bool, int],
        document: Document,
        search: re.Pattern[str],
        match_format: str | None = None,
        doc_key: str | None = None,
        ) -> Any:
    return res[0]


def test_docmatcher(tmp_config: TemporaryConfiguration) -> None:
    from papis.docmatcher import DocumentMatcher, make_document_matcher

    matcher = make_document_matcher("author:einstein")
    assert isinstance(matcher, DocumentMatcher)
    assert matcher.search == "author:einstein"
    assert matcher.query is not None

    docs = get_docs()
    assert len(list(docs)) == 16

    from dataclasses import replace

    matcher = make_document_matcher("author:seitz")
    for res in [(True, 16), (False, 0)]:
        matcher = replace(matcher, matcher=partial(docmatcher_matcher, res))
        filtered = [doc for doc in map(matcher, docs) if doc is not None]
        assert len(filtered) == res[1]


def test_parse_query(tmp_config: TemporaryConfiguration) -> None:
    from papis.docmatcher import parse_query

    rs = parse_query("hello   author : einstein")
    assert rs[0].search == "hello"
    assert rs[1].doc_key == "author"
    assert rs[1].search == "einstein"

    r, = parse_query("doi : 123.123/124_123")
    assert r.doc_key == "doi"
    assert r.search == "123.123/124_123"

    r, = parse_query("doi : 123.123/124_123(80)12")
    assert r.doc_key == "doi"
    assert r.search == "123.123/124_123(80)12"

    rs = parse_query('tt : asfd   author : "Albert einstein"')
    assert rs[0].doc_key == "tt"
    assert rs[0].search == "asfd"
    assert rs[1].doc_key == "author"
    assert rs[1].search == "Albert einstein"
