import pytest
from papis.testing import TemporaryConfiguration

ARXIV_TEST_URLS = [
    ("/URI(https://arxiv.org/abs/1305.2291v2)>>", "1305.2291v2"),
    ("/URI(https://arxiv.org/abs/1205.0093)>>", "1205.0093"),
    ("/URI(https://arxiv.org/abs/1205.1494)>>", "1205.1494"),
    ("/URI(https://arxiv.org/abs/1011.2840)>>", "1011.2840"),
    ("/URI(https://arxiv.org/abs/1110.3658)>>", "1110.3658"),
    ("https://arxiv.org/abs/1110.3658>", "1110.3658"),
    ("http://arxiv.org/abs/1110.3658>", "1110.3658"),
    ("https://arxiv.com/abs/1110.3658>", "1110.3658"),
    ("https://arxiv.org/1110.3658>", "1110.3658"),
    ("arXiv:1701.08223v2?234", "1701.08223v2"),
    ("https://arxiv.org/pdf/1110.3658.pdf", "1110.3658"),
    ("http://arxiv.org/pdf/1110.3658.pdf", "1110.3658"),
    ("https://arxiv.com/pdf/1110.3658.pdf", "1110.3658"),
    ("http://arxiv.com/pdf/1110.3658.pdf", "1110.3658"),
]


@pytest.mark.xfail(reason="arxiv times out sometimes")
def test_get_data(tmp_config: TemporaryConfiguration) -> None:
    from papis.arxiv import get_data
    data = get_data(
        author="Garnet Chan",
        max_results=1,
        title="Finite Temperature"
    )

    assert data
    assert len(data) == 1


def test_find_arxiv_id(tmp_config: TemporaryConfiguration) -> None:
    from papis.arxiv import find_arxivid_in_text

    for url, arxivid in ARXIV_TEST_URLS:
        assert find_arxivid_in_text(url) == arxivid, (
            f"Could not retrieve correct arxivid from {url}")


def test_downloader_match(tmp_config: TemporaryConfiguration) -> None:
    from papis.arxiv import Downloader, ARXIV_ABS_URL

    down = Downloader.match("arxiv.org/sdf")
    assert isinstance(down, Downloader)

    down = Downloader.match("arxiv.com/!@#!@$!%!@%!$chemed.6b00559")
    assert down is None

    for uri, arxivid in ARXIV_TEST_URLS[-2:]:
        down = Downloader.match(uri)
        assert down
        assert down.arxivid == arxivid
        assert down.uri == f"{ARXIV_ABS_URL}/{arxivid}"


@pytest.mark.xfail(reason="arxiv times out sometimes")
@pytest.mark.parametrize("url", [
    "https://arxiv.org/abs/1001.3032",
    "https://arxiv.org/abs/1001.3032vunknown",
    ])
def test_importer_downloader_fetch(tmp_config: TemporaryConfiguration,
                                   url: str) -> None:
    from papis.downloaders import get_matching_downloaders

    downs = get_matching_downloaders(url)
    assert len(downs) >= 1

    down = downs[0]
    assert down.name == "arxiv"
    assert down.expected_document_extensions == ("pdf",)

    doc = down.get_document_data()
    if down.result:
        assert doc is not None
        assert down.check_document_format()
    else:
        assert down.arxivid is not None
        assert doc is None


@pytest.mark.xfail(reason="arxiv times out sometimes")
def test_validate_arxivid(tmp_config: TemporaryConfiguration) -> None:
    from papis.arxiv import validate_arxivid
    # good
    validate_arxivid("1206.6272")
    validate_arxivid("1206.6272v1")
    validate_arxivid("1206.6272v2")

    # bad
    for bad in ["1206.6272v3", "blahv2"]:
        with pytest.raises(ValueError, match="not an arxivid"):
            validate_arxivid(bad)
