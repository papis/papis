from papis.docmatcher import parse_query, DocMatcher
import os
import yaml


def get_docs():
    yamlfile = os.path.join(os.path.dirname(__file__), "data", "licl.yaml")
    with open(yamlfile) as f:
        return list(yaml.safe_load_all(f))


def test_docmatcher():
    DocMatcher.set_search("author:einstein")
    assert DocMatcher.search == "author:einstein"
    DocMatcher.set_search("author:seitz")
    assert DocMatcher.search == "author:seitz"

    DocMatcher.parse()
    assert DocMatcher.parsed_search is not None
    docs = get_docs()
    assert len(list(docs)) == 16
    for res in [(True, 16), (False, 0)]:
        DocMatcher.set_matcher(lambda doc, search, sformat, doc_key, res=res: res[0])
        filtered = list(
            filter(lambda x: x is not None, map(DocMatcher.return_if_match, docs)))
        assert len(filtered) == res[1]


def test_parse_query():
    r = parse_query("hello   author : einstein")
    assert r[0].search == "hello"
    assert r[1].doc_key == "author"
    assert r[1].search == "einstein"

    r, = parse_query("doi : 123.123/124_123")
    assert r.doc_key == "doi"
    assert r.search == "123.123/124_123"

    r, = parse_query("doi : 123.123/124_123(80)12")
    assert r.doc_key == "doi"
    assert r.search == "123.123/124_123(80)12"

    r = parse_query('tt : asfd   author : "Albert einstein"')
    assert r[0].doc_key == "tt"
    assert r[0].search == "asfd"
    assert r[1].doc_key == "author"
    assert r[1].search == "Albert einstein"
