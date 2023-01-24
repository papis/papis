import os
import json
from typing import Any, Dict

import pytest

import tests.downloaders as testlib


def _get_test_json(filename: str) -> Dict[str, Any]:
    resources = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "resources", "crossref"
    )
    filepath = os.path.join(resources, filename)
    with open(filepath) as fd:
        return json.load(fd)


@testlib.with_default_config
@pytest.mark.xfail(reason="crossref times out quite often")
def test_get_data() -> None:
    from papis.crossref import get_data

    data = get_data(
        author="Albert Einstein",
        max_results=1,
    )
    assert data
    assert len(data) == 1


@testlib.with_default_config
@pytest.mark.parametrize(("doi", "basename"), [
    ("10.1103/physrevb.89.140501", "test1"),
    ("10.1103/physrevb.89.140501", "test_2"),
    ("10.1145/3184558.3186235", "test_conference")
    ])
def test_doi_to_data(monkeypatch, doi: str, basename: str) -> None:
    infile = "{}.json".format(basename)
    outfile = "{}_out.json".format(basename)

    import papis.crossref

    with monkeypatch.context() as m:
        m.setattr(papis.crossref,
                  "_get_crossref_works",
                  lambda **x: _get_test_json(infile))

        data = papis.crossref.doi_to_data(doi)
        result = _get_test_json(outfile)

        assert data == result
