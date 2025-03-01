import os
import sys
import pytest
import tempfile

from papis.testing import TemporaryConfiguration


def test_get_cache_home(tmp_config: TemporaryConfiguration, monkeypatch) -> None:
    import papis.config
    from papis.utils import get_cache_home

    assert get_cache_home() == os.path.join(tmp_config.tmpdir, "papis")
    with tempfile.TemporaryDirectory(dir=tmp_config.tmpdir) as d:
        tmp = os.path.join(d, "blah")
        papis.config.set("cache-dir", papis.config.escape_interp(tmp))
        assert get_cache_home() == tmp


@pytest.mark.skipif(sys.platform != "linux", reason="uses linux tools")
def test_general_open_with_spaces(tmp_config: TemporaryConfiguration) -> None:
    suffix = "File with at least a couple of spaces"
    with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix=suffix, delete=False
            ) as f:
        filename = f.name
        f.write("Some content")

    assert os.path.exists(filename)

    from papis.utils import general_open
    general_open(
        filename,
        "nonexistentoption",
        default_opener="sed -i s/o/u/g",
        wait=True
    )

    with open(filename, encoding="utf-8") as fd:
        content = fd.read()

    assert content == "Sume cuntent"
    os.unlink(filename)


def test_locate_document(tmp_config: TemporaryConfiguration) -> None:
    from papis.document import from_data
    docs = [
        from_data({"doi": "10.1021/ct5004252", "title": "Hello world"}),
        from_data(
            {
                "doi": "10.123/12afad12",
                "author": "no one really",
                "title": "Hello world"
            }
        ),
    ]

    from papis.utils import locate_document

    doc = from_data({"doi": "10.1021/CT5004252"})
    found_doc = locate_document(doc, docs)
    assert found_doc is not None

    doc = from_data({"doi": "CT5004252"})
    found_doc = locate_document(doc, docs)
    assert found_doc is None

    doc = from_data({"author": "no one really"})
    found_doc = locate_document(doc, docs)
    assert found_doc is None

    doc = from_data({"title": "Hello world"})
    found_doc = locate_document(doc, docs)
    assert found_doc is None


def test_extension(tmp_config: TemporaryConfiguration) -> None:
    docs = [
        [tmp_config.create_random_file("pdf"), "pdf"],
        [tmp_config.create_random_file("pdf"), "pdf"],
        [tmp_config.create_random_file("epub"), "epub"],
        [tmp_config.create_random_file("text"), "data"],
        [tmp_config.create_random_file("djvu"), "djvu"],
        [tmp_config.create_random_file("text", suffix=".yaml"), "yaml"],
        [tmp_config.create_random_file("text", suffix=".text"), "text"],
    ]

    from papis.filetype import get_document_extension
    for d in docs:
        assert get_document_extension(d[0]) == d[1]


def test_yaml_unicode_dump(tmp_config: TemporaryConfiguration) -> None:
    from papis.crossref import get_data

    doi = "10.1111/febs.15572"
    doc, = get_data(dois=[doi])
    assert doc["doi"] == doi

    from papis.yaml import data_to_yaml, yaml_to_data

    filename = os.path.join(tmp_config.tmpdir, "test_dump_encoding.yml")
    data_to_yaml(filename, doc)

    doc = yaml_to_data(filename)
    assert doc["doi"] == doi
