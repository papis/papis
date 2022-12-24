import os
import pytest

import papis.isbn


@pytest.mark.xfail(reason="sometimes makes too many requests")
def test_get_data():
    mattuck = papis.isbn.get_data(query="Mattuck feynan diagrams")
    assert mattuck
    assert isinstance(mattuck, list)
    assert isinstance(mattuck[0], dict)
    assert mattuck[0]["isbn-13"] == "9780486670478"


def test_importer_match():
    assert papis.isbn.Importer.match("9780486670478")
    assert papis.isbn.Importer.match("this-is-not-an-isbn") is None

    # NOTE: ISBN for Wesseling - An Introduction to Multigrid Methods
    importer = papis.isbn.Importer.match("9781930217089")
    assert importer
    assert importer.uri == "9781930217089"


def load_json(filename, data_getter=None):
    import json
    path = os.path.join(
        os.path.dirname(__file__), "resources", "isbn", filename)

    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
    else:
        data = data_getter()
        with open(path, "w") as f:
            json.dump(data, f, indent=4, sort_keys=True)

    return data


def get_unmodified_isbn_data(query):
    import isbnlib
    isbn = isbnlib.isbn_from_words(query)
    data = isbnlib.meta(isbn, service="openl")
    assert data is not None

    return data


@pytest.mark.parametrize("basename", ["test_isbn_1"])
def test_isbn_to_papis(basename):
    data = load_json(
        "{}.json".format(basename),
        data_getter=lambda: get_unmodified_isbn_data("9781930217089"))

    to_papis_data = papis.isbn.data_to_papis(data)
    result = load_json(
        "{}_out.json".format(basename),
        data_getter=lambda: to_papis_data)

    assert to_papis_data == result
