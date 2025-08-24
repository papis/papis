import pytest

from papis.testing import TemporaryConfiguration


@pytest.mark.xfail(reason="remote pmid validity check can timeout")
def test_match(tmp_config: TemporaryConfiguration) -> None:
    from papis.importer.pubmed import PubMedImporter

    assert PubMedImporter.match("28012456")
    assert PubMedImporter.match("5503630")
    assert PubMedImporter.match("   1397  ")
    assert PubMedImporter.match("ABC1") is None
    assert PubMedImporter.match("1ABC") is None
