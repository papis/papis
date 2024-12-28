import os
from typing import Any, Callable, Optional

import pytest
from papis.testing import TemporaryConfiguration


def load_json(filename: str, data_getter: Optional[Callable[[], Any]] = None) -> Any:
    import json
    path = os.path.join(
        os.path.dirname(__file__), "resources", "isbn", filename)

    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    elif data_getter is not None:
        data = data_getter()
        with open(path, "w") as f:
            json.dump(data, f, indent=4, sort_keys=True)
    else:
        raise ValueError("Must provide a filename or a getter")

    return data


def get_unmodified_isbn_data(query: str) -> Any:
    import isbnlib

    isbn = isbnlib.isbn_from_words(query)
    data = isbnlib.meta(isbn, service="openl")
    assert data is not None

    return data


@pytest.mark.xfail(reason="sometimes makes too many requests")
def test_get_data(tmp_config: TemporaryConfiguration) -> None:
    import papis.isbn

    result = papis.isbn.get_data(query="Mattuck feynan diagrams")
    assert result
    assert isinstance(result, list)
    assert isinstance(result[0], dict)
    assert result[0]["isbn-13"] == "9780486670478"
    assert result[0]["language"] != ""


def test_importer_match(tmp_config: TemporaryConfiguration) -> None:
    import papis.isbn

    assert papis.isbn.Importer.match("9780486670478")
    assert papis.isbn.Importer.match("this-is-not-an-isbn") is None

    # NOTE: ISBN for Wesseling - An Introduction to Multigrid Methods
    importer = papis.isbn.Importer.match("9781930217089")
    assert importer
    assert importer.uri == "9781930217089"


@pytest.mark.parametrize("basename", ["test_isbn_1"])
def test_isbn_to_papis(tmp_config: TemporaryConfiguration, basename: str) -> None:
    import papis.isbn

    data = load_json(
        f"{basename}.json",
        data_getter=lambda: get_unmodified_isbn_data("9781930217089"))

    to_papis_data = papis.isbn.data_to_papis(data)
    result = load_json(
        f"{basename}_out.json",
        data_getter=lambda: to_papis_data)

    assert to_papis_data == result
