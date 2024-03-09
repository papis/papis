import json
import os

from typing import Any, Dict

import pytest
import papis.zenodo
import papis.yaml


def _get_test_json(filename: str) -> Dict[str, Any]:
    resources = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "resources", "zenodo"
    )
    filepath = os.path.join(resources, filename)
    with open(filepath) as fd:
        result = json.load(fd)

    assert isinstance(result, dict)
    return result


@pytest.mark.parametrize(("zenodo_id",), [("7391177",), ("10794563",)])
def test_zenodo_id_to_data(monkeypatch: Any, zenodo_id: str) -> None:
    mock_data_file = "{}.json".format(zenodo_id)
    expected_data_file = "{}_out.json".format(zenodo_id)

    monkeypatch.setattr(
        papis.zenodo, "get_data", lambda x: _get_test_json(mock_data_file)
    )

    input_data = papis.zenodo.get_data(zenodo_id)
    actual_data = papis.zenodo.zenodo_data_to_papis_data(input_data)

    expected_data = _get_test_json(expected_data_file)

    assert expected_data == actual_data
