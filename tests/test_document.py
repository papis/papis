import tempfile
import pickle
import os

import pytest

import papis.document
from papis.testing import TemporaryConfiguration

DOCUMENT_RESOURCES = os.path.join(os.path.dirname(__file__), "resources")


def test_new(tmp_config: TemporaryConfiguration) -> None:
    nfiles = 10
    files = [tmp_config.create_random_file() for _ in range(nfiles)]

    tmp = os.path.join(tmp_config.tmpdir, "doc1")
    doc = papis.document.new(tmp, {"author": "hello"}, files)

    folder = doc.get_main_folder()
    assert folder is not None
    assert os.path.exists(folder)
    assert folder == tmp

    files = doc.get_files()
    assert len(files) == nfiles
    assert all(os.path.exists(f) for f in files)

    tmp = os.path.join(tmp_config.tmpdir, "doc2")
    doc = papis.document.new(tmp, {"author": "hello"}, [])
    folder = doc.get_main_folder()

    assert folder is not None
    assert os.path.exists(folder)
    assert folder == tmp
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
    assert set(doc.keys()) == {"title", "author"}
    assert not doc.has("doi")

    doc["doi"] = "123123.123123"
    assert doc.has("doi")

    del doc["doi"]
    assert not doc.has("doi")
    assert doc["doi"] == ""
    assert set(doc.keys()) == {"title", "author"}

    doc.set_folder(os.path.join(DOCUMENT_RESOURCES, "document"))
    folder = doc.get_main_folder()
    assert folder is not None
    assert doc.get_main_folder_name()
    assert os.path.exists(folder)
    assert doc["author"] == "Turing, Alan"

    doc.load()
    assert doc["author"] == "Russell, Bertrand"
    assert doc.get_files()
    assert isinstance(doc.get_files(), list)
    assert doc.html_escape["author"] == "Russell, Bertrand"


def test_to_bibtex(tmp_config: TemporaryConfiguration) -> None:
    import papis.config
    import papis.bibtex

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
        "@book{Hello_Fernan_3200BCE,\n"
        "  author = {Fernandez, Gilgamesh},\n"
        "  journal = {jcp},\n"
        "  title = {Hello},\n"
        "  year = {3200BCE},\n"
        "}")
    doc["journal_abbrev"] = "j"
    assert papis.bibtex.to_bibtex(doc) == (
        "@book{Hello_Fernan_3200BCE,\n"
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


def test_sort(tmp_config: TemporaryConfiguration) -> None:
    docs = [
        papis.document.from_data({"title": "Hello world", "year": 1990}),
        papis.document.from_data({"author": "Turing", "year": "1932"}),
    ]
    sdocs = papis.document.sort(docs, key="year", reverse=False)
    assert sdocs[0] == docs[1]


def test_dump(tmp_config: TemporaryConfiguration) -> None:
    doc = papis.document.from_data({
        "author": "Turing, Alan",
        "title": "Computing machinery and intelligence",
        "year": 1950,
        "some-longer-key": "value",
        })

    result = papis.document.dump(doc)
    expected_result = (
        "author: Turing, Alan\n"
        "some-longer-key: value\n"
        "title: Computing machinery and intelligence\n"
        "year: 1950"
        )

    assert result == expected_result


@pytest.mark.parametrize("formatter", ["python", "jinja2"])
def test_multiple_authors_separator(tmp_config: TemporaryConfiguration,
                                    formatter: str) -> None:
    # Test fix for https://github.com/papis/papis/issues/905
    papis.config.set("formatter", formatter)

    if formatter == "jinja2":
        pytest.importorskip("jinja2")
        multiple_authors_format = "{{ au.family }}"
    elif formatter == "python":
        multiple_authors_format = "{au[family]}"
    else:
        raise ValueError(f"Unknown formatter: '{formatter}'")

    data = {
        "author_list": [
            {"family": "Cox", "given": "David"},
            {"family": "Little", "given": "John"},
            {"family": "O'Shea", "given": "Donald"}
        ],
        "publisher": "Springer",
        "title": "Ideals, Varieties, and Algorithms",
        "type": "book",
        "year": 2015
    }

    from papis.document import author_list_to_author

    result = author_list_to_author(data, separator=" and ",
                                   multiple_authors_format=multiple_authors_format)

    assert result == "Cox and Little and O'Shea"


def test_author_separator_heuristics(tmp_config: TemporaryConfiguration) -> None:
    import re
    from papis.document import guess_authors_separator, split_authors_name

    def is_comma_and_re(sep: str) -> None:
        assert sep
        assert re.match(sep, ", and")
        assert re.match(sep, ",and")
        assert re.match(sep, ",")

    s = "Sanger, F. and Nicklen, S. and Coulson, A. R."
    expected = [{"family": "Sanger", "given": "F."},
                {"family": "Nicklen", "given": "S."},
                {"family": "Coulson", "given": "A. R."}]
    assert guess_authors_separator(s) == "and"
    assert split_authors_name([s]) == expected

    expected = [{"family": "Sanger", "given": "Fabian"},
                {"family": "Nicklen", "given": "Steven"},
                {"family": "Coulson", "given": "Alexander R."}]

    s = "Fabian Sanger and Steven Nicklen and Alexander R. Coulson"
    assert guess_authors_separator(s) == "and"
    assert split_authors_name([s]) == expected

    s = "Fabian Sanger, Steven Nicklen, Alexander R. Coulson"
    assert guess_authors_separator(s) == ","
    assert split_authors_name([s]) == expected

    s = "Fabian Sanger, and Steven Nicklen, and Alexander R. Coulson"
    sep = guess_authors_separator(s)
    is_comma_and_re(sep)
    assert split_authors_name([s]) == expected

    s = "Fabian Sanger, Steven Nicklen, and Alexander R. Coulson"
    sep = guess_authors_separator(s)
    is_comma_and_re(sep)
    assert split_authors_name([s]) == expected

    expected = [{"family": "Doe", "given": "John"},
                {"family": "Dorian", "given": "Jane"},
                {"family": "Unknown", "given": "James T."}]

    s = "John Doe, Jane Dorian, and James T. Unknown "
    sep = guess_authors_separator(s)
    is_comma_and_re(sep)
    assert split_authors_name([s]) == expected

    expected = [{"family": "Duck", "given": "Dagobert"},
                {"family": "von Beethoven", "given": "Ludwig"},
                {"family": "Ford Jr.", "given": "Henry"}]

    s = "Dagobert Duck and von Beethoven, Ludwig and Ford, Jr., Henry"
    assert guess_authors_separator(s) == "and"
    assert split_authors_name([s]) == expected

    expected = [{"family": "Turing", "given": "A. M."}]

    s = "Turing, A. M."
    assert guess_authors_separator(s) == "and"
    assert split_authors_name([s]) == expected

    expected = [{"family": "Liddel Hart", "given": "Basil"}]

    s = "Liddel Hart, Basil"
    assert guess_authors_separator(s) == "and"
    assert split_authors_name([s]) == expected

    # NOTE: we cannot usefully distinguish between these cases:
    #   s = "Last Last, First"        # one author
    #   s = "Last, First First"       # one author
    #   s = "Last Last, First First"  # one author
    #   s = "First Last, First Last"  # two authors
