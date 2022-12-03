import tempfile
import pickle
import os

import papis.bibtex
import papis.config
import papis.format
import papis.document

from tests import create_random_file

DOCUMENT_RESOURCES = os.path.join(os.path.dirname(__file__), "resources")


def test_new() -> None:
    nfiles = 10
    files = [create_random_file(suffix=".{}".format(i)) for i in range(nfiles)]

    with tempfile.TemporaryDirectory() as d:
        tmp = os.path.join(d, "doc")
        doc = papis.document.new(tmp, {"author": "hello"}, files)

        assert os.path.exists(doc.get_main_folder())
        assert doc.get_main_folder() == tmp
        assert len(doc["files"]) == nfiles
        assert len(doc.get_files()) == nfiles

        for i in range(nfiles):
            assert doc["files"][i].endswith(str(i))
            assert not os.path.exists(doc["files"][i])
            assert os.path.exists(doc.get_files()[i])

    with tempfile.TemporaryDirectory() as d:
        tmp = os.path.join(d, "doc")
        doc = papis.document.new(tmp, {"author": "hello"}, [])

        assert os.path.exists(doc.get_main_folder())
        assert doc.get_main_folder() == tmp
        assert len(doc["files"]) == 0
        assert len(doc.get_files()) == 0


def test_from_data() -> None:
    doc = papis.document.from_data({"title": "Hello World", "author": "turing"})
    assert isinstance(doc, papis.document.Document)


def test_from_folder() -> None:
    doc = papis.document.from_folder(os.path.join(DOCUMENT_RESOURCES, "document"))
    assert isinstance(doc, papis.document.Document)
    assert doc["author"] == "Russell, Bertrand"


def test_main_features() -> None:
    doc = papis.document.from_data({
        "title": "Hello World",
        "author": "Turing, Alan",
        })

    assert doc.has("title")
    assert doc["title"] == "Hello World"
    assert set(doc.keys()) == set(["title", "author"])
    assert not doc.has("doi")

    doc["doi"] = "123123.123123"
    assert doc.has("doi")

    del doc["doi"]
    assert not doc.has("doi")
    assert doc["doi"] == ""
    assert set(doc.keys()) == set(["title", "author"])

    doc.set_folder(os.path.join(DOCUMENT_RESOURCES, "document"))
    assert doc.get_main_folder_name()
    assert os.path.exists(doc.get_main_folder())
    assert doc["author"] == "Turing, Alan"

    doc.load()
    assert doc["author"] == "Russell, Bertrand"
    assert doc.get_files()
    assert isinstance(doc.get_files(), list)
    assert doc.html_escape["author"] == "Russell, Bertrand"


def test_to_bibtex() -> None:
    papis.config.set("bibtex-journal-key", "journal_abbrev")
    doc = papis.document.from_data({
        "title": "Hello",
        "author": "Fernandez, Gilgamesh",
        "year": "3200BCE",
        "type": "book",
        "journal": "jcp",
        })
    doc.set_folder("path/to/superfolder")

    assert papis.bibtex.to_bibtex(doc) == (
        "@book{HelloFernan3200bce,\n"
        "  author = {Fernandez, Gilgamesh},\n"
        "  journal = {jcp},\n"
        "  title = {Hello},\n"
        "  year = {3200BCE},\n"
        "}")
    doc["journal_abbrev"] = "j"
    assert papis.bibtex.to_bibtex(doc) == (
        "@book{HelloFernan3200bce,\n"
        "  author = {Fernandez, Gilgamesh},\n"
        "  journal = {j},\n"
        "  title = {Hello},\n"
        "  year = {3200BCE},\n"
        "}")
    del doc["title"]

    doc["ref"] = "hello1992"
    assert papis.bibtex.to_bibtex(doc) == (
        "@book{hello1992,\n"
        "  author = {Fernandez, Gilgamesh},\n"
        "  journal = {j},\n"
        "  year = {3200BCE},\n"
        "}")


def test_to_json() -> None:
    doc = papis.document.from_data({"title": "Hello World"})
    assert papis.document.to_json(doc) == '{"title": "Hello World"}'


def test_pickle() -> None:
    docs = [
        papis.document.from_data({"title": "Hello World"}),
        papis.document.from_data({"author": "Turing"}),
    ]

    with tempfile.TemporaryFile() as fd:
        pickle.dump(docs, fd)
        fd.seek(0)
        gotdocs = pickle.load(fd)

    assert gotdocs[0]["title"] == docs[0]["title"]
    assert gotdocs[1]["author"] == docs[1]["author"]


def test_sort() -> None:
    docs = [
        papis.document.from_data(dict(title="Hello world", year=1990)),
        papis.document.from_data({"author": "Turing", "year": "1932"}),
    ]
    sdocs = papis.document.sort(docs, key="year", reverse=False)
    assert sdocs[0] == docs[1]


def test_dump() -> None:
    doc = papis.document.from_data({
        "author": "Turing, Alan",
        "title": "Computing machinery and intelligence",
        "year": 1950,
        "some-longer-key": "value",
        })

    result = papis.document.dump(doc)
    expected_result = (
        "author:            Turing, Alan\n"
        "some-longer-key:   value\n"
        "title:             Computing machinery and intelligence\n"
        "year:              1950"
        )

    assert result == expected_result
