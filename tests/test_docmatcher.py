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
        DocMatcher.set_matcher(lambda doc, search, sformat, res=res: res[0])
        filtered = list(
            filter(lambda x: x is not None, map(DocMatcher.return_if_match, docs)))
        assert len(filtered) == res[1]


def test_parse_query():
    r = parse_query("hello   author : einstein")
    assert r[0][0] == "hello"
    assert r[1][0] == "author"
    assert r[1][1] == ":"
    assert r[1][2] == "einstein"

    r = parse_query("doi : 123.123/124_123")
    re = ["doi", ":", "123.123/124_123"]
    for i in range(len(re)):
        assert r[0][i] == re[i]

    r = parse_query("doi : 123.123/124_123(80)12")
    re = ["doi", ":", "123.123/124_123(80)12"]
    for i in range(len(re)):
        assert r[0][i] == re[i]

    r = parse_query('tt : asfd   author : "Albert einstein"')
    assert r[0][0] == "tt"
    assert r[0][1] == ":"
    assert r[0][2] == "asfd"
    assert r[1][0] == "author"
    assert r[1][1] == ":"
    assert r[1][2] == "Albert einstein"
