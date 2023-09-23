import os

from papis.testing import TemporaryLibrary


def test_exporter(tmp_library: TemporaryLibrary) -> None:
    import papis.database

    db = papis.database.get()
    doc, = db.query_dict({"author": "turing"})
    filename = os.path.join(os.path.dirname(__file__),
                            "resources", "hayagriva_1_out.yml")

    from papis.hayagriva import to_hayagriva
    result = to_hayagriva(doc)

    from papis.yaml import yaml_to_data
    expected = yaml_to_data(filename)

    assert result == expected
