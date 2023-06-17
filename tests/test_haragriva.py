import os

import papis.yaml
import papis.hayagriva

from tests.testlib import TemporaryLibrary


def test_exporter(tmp_library: TemporaryLibrary) -> None:
    db = papis.database.get()
    doc, = db.query_dict({"author": "turing"})

    filename = os.path.join(os.path.dirname(__file__),
                            "resources", "hayagriva_1_out.yml")
    result = papis.hayagriva.to_hayagriva(doc)
    expected = papis.yaml.yaml_to_data(filename)

    assert result == expected
