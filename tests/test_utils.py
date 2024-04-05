import os
import sys
import pytest
import tempfile

from papis.testing import TemporaryConfiguration


@pytest.mark.skipif(sys.platform != "linux", reason="uses linux paths")
def test_get_cache_home(tmp_config: TemporaryConfiguration, monkeypatch) -> None:
    import papis.config
    from papis.utils import get_cache_home
    tmpdir = tempfile.gettempdir()

    with monkeypatch.context() as m:
        m.delenv("XDG_CACHE_HOME", raising=False)
        assert get_cache_home() == os.path.join(os.path.expanduser("~/.cache"), "papis")

    with monkeypatch.context() as m:
        m.setenv("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
        assert get_cache_home() == os.path.join(os.environ["XDG_CACHE_HOME"], "papis")

    with monkeypatch.context() as m:
        m.setenv("XDG_CACHE_HOME", os.path.join(tmpdir, ".cache"))

        assert get_cache_home() == os.path.join(tmpdir, ".cache", "papis")
        assert os.path.exists(get_cache_home())

    with tempfile.TemporaryDirectory(dir=tmp_config.tmpdir) as d:
        tmp = os.path.join(d, "blah")
        papis.config.set("cache-dir", tmp)
        assert get_cache_home() == tmp


def test_create_identifier() -> None:
    import string
    from papis.utils import create_identifier

    expected = [
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
        "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
        "AA", "AB", "AC", "AD"
    ]
    for value, output in zip(expected, create_identifier(string.ascii_uppercase)):
        assert output == value


@pytest.mark.skipif(sys.platform != "linux", reason="uses linux tools")
def test_general_open_with_spaces(tmp_config: TemporaryConfiguration) -> None:
    suffix = "File with at least a couple of spaces"
    with tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False) as f:
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

    with open(filename) as fd:
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


def test_slugify(tmp_config: TemporaryConfiguration) -> None:
    from papis.utils import clean_document_name

    assert (
        clean_document_name("{{] __ }}albert )(*& $ß $+_ einstein (*]")
        == "albert-ss-einstein"
    )
    assert (
        clean_document_name('/ashfd/df/  #$%@#$ }{_+"[ ]hello öworld--- .pdf')
        == "hello-oworld-.pdf"
    )
    assert clean_document_name("масса и енергиа.pdf") == "massa-i-energia.pdf"
    assert clean_document_name("الامير الصغير.pdf") == "lmyr-lsgyr.pdf"


def test_slugify_config(tmp_config: TemporaryConfiguration) -> None:
    import papis.config

    from papis.utils import clean_document_name

    papis.config.set("doc-paths-lowercase", "False")
    assert (
        clean_document_name("{{] __ }}Albert )(*& $ß $+_ Einstein (*]")
        == "Albert-ss-Einstein"
    )

    papis.config.set("doc-paths-extra-chars", "_")
    assert (
        clean_document_name("{{] __ }}Albert )(*& $ß $+_ Einstein (*]")
        == "__-Albert-ss-_-Einstein"
    )
    assert (
        clean_document_name("{{] __Albert )(*& $ß $+_ Einstein (*]")
        == "__Albert-ss-_-Einstein"
    )

    papis.config.set("doc-paths-word-separator", "_")
    assert (
        clean_document_name("{{] __ }}Albert )(*& $ß $+_ Einstein (*]")
        == "___Albert_ss___Einstein"
    )

    papis.config.set("doc-paths-lowercase", "True")
    assert (
        clean_document_name("{{] __ }}Albert )(*& $ß $+_ Einstein (*]")
        == "___albert_ss___einstein"
    )


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
