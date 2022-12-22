import pytest

import papis.pubmed


@pytest.mark.xfail(reason="remote pmid validity check can timeout")
def test_match():
    assert papis.pubmed.Importer.match("28012456")
    assert papis.pubmed.Importer.match("5503630")
    assert papis.pubmed.Importer.match("   1397  ")
    assert papis.pubmed.Importer.match("ABC1") is None
    assert papis.pubmed.Importer.match("1ABC") is None
