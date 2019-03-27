from papis.document import (
    to_bibtex,
    to_json,
    from_folder,
    from_data,
    Document,
)
import tempfile
import papis.config
import pickle
import os


def test_from_data():
    doc = from_data(
        {'title': 'Hello World', 'author': 'turing'}
    )
    assert(isinstance(doc, Document))


def test_from_folder():
    doc = from_folder(os.path.join(
        os.path.dirname(__file__), 'resources', 'document'
    ))
    assert(isinstance(doc, Document))
    assert(doc['author'] == 'Russell, Bertrand')


def test_main_features():
    doc = from_data(
        {'title': 'Hello World', 'author': 'turing'}
    )
    assert(doc.title == 'Hello World')
    assert(doc.title == doc['title'])
    assert(doc.has('title'))
    assert(set(doc.keys()) == set(['title', 'author']))
    assert(not doc.has('doi'))
    doc['doi'] = '123123.123123'
    assert(doc.has('doi'))
    assert(doc.doi == doc['doi'])
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


def test_to_bibtex():
    papis.config.set('bibtex-journal-key', 'journal_abbrev')
    doc = from_data({'title': 'Hello', 'type': 'book', 'journal': 'jcp'})
    doc.set_folder('path/to/superfolder')
    assert(
        to_bibtex(doc) ==
        '@book{superfolder,\n  journal = {jcp},\n  title = {Hello},\n  type = {book},\n}\n'
    )
    doc['journal_abbrev'] = 'j'
    assert(
        to_bibtex(doc) ==
        '@book{superfolder,\n  journal = {j},\n  title = {Hello},\n  type = {book},\n}\n'
    )
    del doc['title']
    doc['ref'] = 'hello1992'
    assert(
        to_bibtex(doc) ==
        '@book{hello1992,\n  journal = {j},\n  type = {book},\n}\n'
    )


def test_to_json():
    doc = from_data({'title': 'Hello World'})
    assert(
        to_json(doc) ==
        '{"title": "Hello World"}'
    )


def test_pickle():
    docs = [
        from_data({'title': 'Hello World'}),
        from_data({'author': 'Turing'}),
    ]
    filepath = tempfile.mktemp()
    with open(filepath, 'wb+') as fd:
        pickle.dump(docs, fd)

    with open(filepath, 'rb') as fd:
        gotdocs = pickle.load(fd)

    assert(gotdocs[0].title == docs[0].title)
    assert(gotdocs[1].author == docs[1].author)
