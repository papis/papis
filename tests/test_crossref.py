import os
from unittest.mock import patch
import json
from papis.crossref import (
    get_data, doi_to_data
)


def _get_test_json(filename):
    resources = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'resources', 'crossref'
    )
    filepath = os.path.join(resources, filename)
    with open(filepath) as fd:
        return json.load(fd)


def test_get_data():
    data = get_data(
        author='Albert Einstein',
        max_results=1,
    )
    assert(data)
    assert(len(data) == 1)


@patch(
    'papis.crossref._get_crossref_works',
    lambda **x: _get_test_json('test1.json')
)
def test_doi_to_data():
    data = doi_to_data('10.1103/physrevb.89.140501')
    assert(isinstance(data, dict))
    result = _get_test_json('test1_out.json')
    assert(result == data)


@patch(
    'papis.crossref._get_crossref_works',
    lambda **x: _get_test_json('test_conference.json')
)
def test_doi_to_data_conference():
    data = doi_to_data('')
    assert(isinstance(data, dict))
    result = _get_test_json('test_conference_out.json')
    assert(result == data)
