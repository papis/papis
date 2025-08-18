import os

import pytest

from papis.testing import TemporaryLibrary


def test_simple(tmp_library: TemporaryLibrary) -> None:
    import papis.database

    db = papis.database.get()
    doc, = db.query_dict({"author": "turing"})
    filename = os.path.join(os.path.dirname(__file__),
                            "resources", "hayagriva_1_out.yml")

    from papis.exporters.typst import to_hayagriva
    result = to_hayagriva(doc)

    from papis.yaml import yaml_to_data
    expected = yaml_to_data(filename)

    assert result == expected


@pytest.mark.parametrize(("author", "editor_count"), [("schrute", 1), ("scott", 2)])
def test_parent_editors(author: str,
                        editor_count: int,
                        tmp_library: TemporaryLibrary) -> None:
    import papis.database
    from papis.exporters.typst import to_hayagriva

    db = papis.database.get()

    doc, = db.query_dict({"author": author})
    result = to_hayagriva(doc)
    assert "parent" in result.keys()
    assert len(result["parent"]["editor"]) == editor_count
