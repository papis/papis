import os
import re
from functools import partial
from typing import Any

import yaml

from papis.document import Document
from papis.testing import TemporaryConfiguration


def get_docs() -> list["Document"]:
    from papis.document import from_data

    yamlfile = os.path.join(os.path.dirname(__file__), "data", "licl.yaml")
    with open(yamlfile, encoding="utf-8") as f:
        return [from_data(data) for data in yaml.safe_load_all(f)]


def docmatcher_matcher(
        res: tuple[bool, int],
        document: "Document",
        search: re.Pattern[str],
        match_format: str | None = None,
        doc_key: str | None = None,
        ) -> Any:
    return res[0]


def test_docmatcher(tmp_config: TemporaryConfiguration) -> None:
    from papis.docmatcher import DocMatcher

    DocMatcher.set_search("author:einstein")
    assert DocMatcher.search == "author:einstein"
    DocMatcher.set_search("author:seitz")
    assert DocMatcher.search == "author:seitz"

    DocMatcher.parse()
    assert DocMatcher.parsed_search is not None

    docs = get_docs()
    assert len(list(docs)) == 16

    for res in [(True, 16), (False, 0)]:
        DocMatcher.set_matcher(partial(docmatcher_matcher, res))
        filtered = list(
            filter(lambda x: x is not None, map(DocMatcher.return_if_match, docs)))
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
