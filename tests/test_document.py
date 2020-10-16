from papis.bibtex import to_bibtex
from papis.document import (
    new,
    to_json,
    from_folder,
    from_data,
    Document,
    sort,
)
import papis.format
import tempfile
import papis.config
import pickle
import os
from tests import create_random_file, setup_test_library
from tests import create_random_file, setup_test_library, create_real_document


def test_new() -> None:
    N = 10
    files = [create_random_file(suffix='.' + str(i)) for i in range(N)]
    tmp = os.path.join(tempfile.mkdtemp(), 'doc')
    doc = new(tmp, {'author': 'hello'}, files)
    assert(os.path.exists(doc.get_main_folder()))
    assert(doc.get_main_folder() == tmp)
    assert(len(doc['files']) == N)
    assert(len(doc.get_files()) == N)
    for i in range(N):
        assert(doc['files'][i].endswith(str(i)))
        assert(not os.path.exists(doc['files'][i]))
        assert(os.path.exists(doc.get_files()[i]))

    tmp = os.path.join(tempfile.mkdtemp(), 'doc')
    doc = new(tmp, {'author': 'hello'}, [])
    assert(os.path.exists(doc.get_main_folder()))
    assert(doc.get_main_folder() == tmp)
    assert(len(doc['files']) == 0)
    assert(len(doc.get_files()) == 0)


def test_from_data() -> None:
    doc = from_data(
        {'title': 'Hello World', 'author': 'turing'}
    )
    assert(isinstance(doc, Document))


def test_from_folder() -> None:
    doc = from_folder(os.path.join(
        os.path.dirname(__file__), 'resources', 'document'
    ))
    assert(isinstance(doc, Document))
    assert(doc['author'] == 'Russell, Bertrand')


def test_main_features() -> None:
    doc = from_data(
        {'title': 'Hello World', 'author': 'turing'}
    )
    assert(doc['title'] == 'Hello World')
    assert(doc['title'] == doc['title'])
    assert(doc.has('title'))
    assert(set(doc.keys()) == set(['title', 'author']))
    assert(not doc.has('doi'))
    doc['doi'] = '123123.123123'
    assert(doc.has('doi'))
    assert(doc['doi'] == doc['doi'])
    del doc['doi']
    assert(doc['doi'] is '')
    assert(set(doc.keys()) == set(['title', 'author']))
    assert(not doc.has('doi'))

    doc.set_folder(os.path.join(
        os.path.dirname(__file__), 'resources', 'document'
    ))
    assert(doc.get_main_folder_name())
    assert(os.path.exists(doc.get_main_folder()))
    assert(doc['author'] == 'turing')
    doc.load()
    assert(doc['author'] == 'Russell, Bertrand')
    assert(doc.get_files())
    assert(isinstance(doc.get_files(), list))
    assert(doc.html_escape['author'] == 'Russell, Bertrand')


def test_to_bibtex() -> None:
    papis.config.set('bibtex-journal-key', 'journal_abbrev')
    doc = from_data({'title': 'Hello',
                     'author': 'Fernandez, Gilgamesh',
                     'year': "3200BCE",
                     'type': 'book',
                     'journal': 'jcp'
                     })
    doc.set_folder('path/to/superfolder')
    assert \
        to_bibtex(doc) == \
        ("@book{HelloFernan3200bce,\n"
         "  author = {Fernandez, Gilgamesh},\n"
         "  journal = {jcp},\n"
         "  title = {Hello},\n"
         "  type = {book},\n"
         "  year = {3200BCE},\n"
         "}\n")
    doc['journal_abbrev'] = 'j'
    assert \
        to_bibtex(doc) == \
        ('@book{HelloFernan3200bce,\n'
         '  author = {Fernandez, Gilgamesh},\n'
         '  journal = {j},\n'
         '  title = {Hello},\n'
         '  type = {book},\n'
         '  year = {3200BCE},\n'
         '}\n')
    del doc['title']
    doc['ref'] = 'hello1992'
    assert(
        to_bibtex(doc) ==
        '@book{hello1992,\n'
        '  journal = {j},\n'
        '  author = {Fernandez, Gilgamesh},\n',
        '  type = {book},\n'
        '  year = {3200BCE},\n'
        '}\n'
    )


def test_to_json() -> None:
    doc = from_data({'title': 'Hello World'})
    assert(
        to_json(doc) ==
        '{"title": "Hello World"}'
    )


def test_pickle() -> None:
    docs = [
        from_data({'title': 'Hello World'}),
        from_data({'author': 'Turing'}),
    ]
    filepath = tempfile.mktemp()
    with open(filepath, 'wb+') as fd:
        pickle.dump(docs, fd)

    with open(filepath, 'rb') as fd:
        gotdocs = pickle.load(fd)

    assert(gotdocs[0]['title'] == docs[0]['title'])
    assert(gotdocs[1]['author'] == docs[1]['author'])


def test_sort() -> None:
    docs = [
        from_data(dict(title="Hello world", year=1990)),
        from_data({'author': 'Turing', 'year': "1932"}),
    ]
    sDocs = sort(docs, key="year", reverse=False)
    assert(sDocs[0] == docs[1])
