from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from papis.testing import TemporaryConfiguration


def test_csv_export_docs(tmp_config: TemporaryConfiguration) -> None:
    import papis.config
    from papis.document import from_data
    from papis.exporters.csv import exporter

    papis.config.set("exporter-csv-keys", ["author", "title"])

    # no docs
    result = exporter([])
    lines = result.splitlines()
    assert len(lines) == 1
    assert lines[0] == '"author","title"'

    # multiple docs
    doc1 = from_data({
        "author": "Alice",
        "author_list": [{"given": "Alice", "family": "Smith"}],
        "title": "Paper One",
    })
    doc2 = from_data({
        "author": "Bob",
        "author_list": [{"given": "Bob", "family": "Jones"}],
        "title": "Paper Two",
    })

    result = exporter([doc1, doc2])
    lines = result.splitlines()
    assert len(lines) == 3
    assert lines[0] == '"author","title"'
    assert "Alice" in lines[1]
    assert "Bob" in lines[2]


def test_csv_export_missing_keys(tmp_config: TemporaryConfiguration) -> None:
    import papis.config
    from papis.document import from_data
    from papis.exporters.csv import exporter

    papis.config.set("exporter-csv-keys", ["title", "doi", "year"])

    doc = from_data({"title": "Missing Fields Paper"})

    result = exporter([doc])
    lines = result.splitlines()
    assert lines[0] == '"title","doi","year"'
    assert lines[1].split(",") == ['"Missing Fields Paper"', '""', '""']


def test_csv_export_list_values(tmp_config: TemporaryConfiguration) -> None:
    import papis.config
    from papis.document import from_data
    from papis.exporters.csv import exporter

    papis.config.set("exporter-csv-keys", ["title", "tags"])

    doc = from_data({
        "title": "Tagged Paper",
        "tags": ["physics", "quantum"],
    })

    result = exporter([doc])
    lines = result.splitlines()
    assert "physics; quantum" in lines[1]


def test_csv_export_default_keys(tmp_config: TemporaryConfiguration) -> None:
    import papis.config
    from papis.bibtex import bibtex_keys
    from papis.document import from_data
    from papis.exporters.csv import exporter

    papis.config.set("exporter-csv-keys", list(bibtex_keys))

    doc = from_data({
        "author": "Test Author",
        "author_list": [{"given": "Test", "family": "Author"}],
        "title": "Test Title",
        "year": 2024,
        "ref": "test2024",
    })

    result = exporter([doc])
    lines = result.splitlines()
    header = lines[0]
    assert '"title"' in header
    assert '"author"' in header
    assert '"year"' in header
    # NOTE: ref is not a BibTeX key, so it will not be exported
    assert '"ref"' not in header
