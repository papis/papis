import os
from typing import Optional

import pytest

from papis.downloaders import get_available_downloaders, get_matching_downloaders
from papis.testing import TemporaryConfiguration


def test_get_available_downloaders(tmp_config: TemporaryConfiguration) -> None:
    downloaders = get_available_downloaders()
    assert len(downloaders) > 0
    for d in downloaders:
        assert d is not None
        assert callable(d.match)


def test_get_downloader(tmp_config: TemporaryConfiguration) -> None:
    down = get_matching_downloaders("arXiv:1701.08223v2")
    assert down is not None
    assert len(down) >= 1
    assert down[0].name == "arxiv"


@pytest.mark.parametrize(("url", "expected_file_name", "ext"), [
    (
        "https://arxiv.org/pdf/2408.03952",
        "2408.03952v1.pdf",
        None
    ),
    (
        "https://arxiv.org/bibtex/2408.03952",
        "2408.03952.bib",
        ".bib"
    ),
    (
        "https://github.com/",
        "github.com.html",
        None
    )
    ])
def test_download_document(tmp_config: TemporaryConfiguration,
                           url: str,
                           expected_file_name: str,
                           ext: Optional[str]) -> None:
    from papis.downloaders import download_document

    local_file_name = download_document(url, expected_document_extension=ext)
    assert os.path.basename(local_file_name) == expected_file_name
