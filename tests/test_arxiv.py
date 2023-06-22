import papis.arxiv
import papis.downloaders

from tests.testlib import TemporaryConfiguration


def test_get_data(tmp_config: TemporaryConfiguration) -> None:
    data = papis.arxiv.get_data(
        author="Garnet Chan",
        max_results=1,
        title="Finite Temperature"
    )

    assert data
    assert len(data) == 1


def test_find_arxiv_id(tmp_config: TemporaryConfiguration) -> None:
    test_data = [
        ("/URI(https://arxiv.org/abs/1305.2291v2)>>", "1305.2291v2"),
        ("/URI(https://arxiv.org/abs/1205.0093)>>", "1205.0093"),
        ("/URI(https://arxiv.org/abs/1205.1494)>>", "1205.1494"),
        ("/URI(https://arxiv.org/abs/1011.2840)>>", "1011.2840"),
        ("/URI(https://arxiv.org/abs/1110.3658)>>", "1110.3658"),
        ("https://arxiv.org/abs/1110.3658>", "1110.3658"),
        ("http://arxiv.org/abs/1110.3658>", "1110.3658"),
        ("https://arxiv.com/abs/1110.3658>", "1110.3658"),
        ("https://arxiv.org/1110.3658>", "1110.3658"),
        ("https://arxiv.org/pdf/1110.3658.pdf", "1110.3658"),
        ("http://arxiv.org/pdf/1110.3658.pdf", "1110.3658"),
        ("https://arxiv.com/pdf/1110.3658.pdf", "1110.3658"),
        ("http://arxiv.com/pdf/1110.3658.pdf", "1110.3658"),
    ]

    for url, arxivid in test_data:
        assert papis.arxiv.find_arxivid_in_text(url) == arxivid, \
            f"Could not retrieve correct arxivid from {url}"


def test_match(tmp_config: TemporaryConfiguration) -> None:
    down = papis.arxiv.Downloader.match("arxiv.org/sdf")
    assert isinstance(down, papis.arxiv.Downloader)

    down = papis.arxiv.Downloader.match("arxiv.com/!@#!@$!%!@%!$chemed.6b00559")
    assert down is None

    down = papis.arxiv.Downloader.match("arXiv:1701.08223v2?234")
    assert isinstance(down, papis.arxiv.Downloader)
    assert down.uri == "https://arxiv.org/abs/1701.08223v2"
    assert down.arxivid == "1701.08223v2"


def test_downloader_getter(tmp_config: TemporaryConfiguration) -> None:
    import papis.bibtex

    url = "https://arxiv.org/abs/1001.3032"
    downs = papis.downloaders.get_matching_downloaders(url)
    assert len(downs) >= 1

    down = downs[0]
    assert down.name == "arxiv"
    assert down.expected_document_extensions == ("pdf",)

    bibtex = down.get_bibtex_data()
    assert bibtex is not None
    assert len(bibtex) > 0

    bibs = papis.bibtex.bibtex_to_dict(bibtex)
    assert len(bibs) == 1

    doc = down.get_document_data()
    assert doc is not None
    assert down.check_document_format()


def test_validate_arxivid(tmp_config: TemporaryConfiguration) -> None:
    # good
    papis.arxiv.validate_arxivid("1206.6272")
    papis.arxiv.validate_arxivid("1206.6272v1")
    papis.arxiv.validate_arxivid("1206.6272v2")

    import pytest
    for bad in ["1206.6272v3", "blahv2"]:
        with pytest.raises(ValueError):
            papis.arxiv.validate_arxivid(bad)
