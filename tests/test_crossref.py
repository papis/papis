import os
import json
from typing import Any, Dict

import pytest
from papis.testing import TemporaryConfiguration


def _get_test_json(filename: str) -> Dict[str, Any]:
    resources = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "resources", "crossref"
    )
    filepath = os.path.join(resources, filename)
    with open(filepath, encoding="utf-8") as fd:
        result = json.load(fd)

    assert isinstance(result, dict)
    return result


@pytest.mark.xfail(reason="crossref times out quite often")
def test_get_data(tmp_config: TemporaryConfiguration) -> None:
    from papis.crossref import get_data

    data = get_data(
        author="Albert Einstein",
        max_results=1,
    )
    assert data
    assert len(data) == 1


@pytest.mark.parametrize(("doi", "basename"), [
    ("10.1103/physrevb.89.140501", "test_1_multiple_authors"),
    ("10.1103/physrevb.89.140501", "test_2_abstract"),
    ("10.1145/3184558.3186235", "test_3_conference"),
    ("10.1007/978-3-0348-8720-5_13", "test_4_multiple_isbn"),
    ])
def test_doi_to_data(tmp_config: TemporaryConfiguration, monkeypatch,
                     doi: str, basename: str) -> None:
    infile = f"{basename}.json"
    outfile = f"{basename}_out.json"

    import papis.crossref

    monkeypatch.setattr(papis.crossref,
                        "_get_crossref_works",
                        lambda **x: _get_test_json(infile))

    data = papis.crossref.doi_to_data(doi)
    result = _get_test_json(outfile)

    assert data == result
