from papis.docmatcher import *


def test_parse_query():
    r = parse_query('hello   author = einstein')
    assert(r[0][0] == 'hello')
    assert(r[1][0] == 'author')
    assert(r[1][1] == '=')
    assert(r[1][2] == 'einstein')

    r = parse_query('doi = 123.123/124_123')
    re = ["doi", "=", "123.123/124_123"]
    for i in range(len(re)):
        assert(r[0][i] == re[i])

    r = parse_query('tt = asfd   author = "Albert einstein"')
    assert(r[0][0] == 'tt'); assert(r[0][1] == '='); assert(r[0][2] == 'asfd')
    assert(r[1][0] == 'author')
    assert(r[1][1] == '=')
    assert(r[1][2] == 'Albert einstein')

