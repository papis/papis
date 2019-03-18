from papis.document import *
import tempfile
import papis.config
import pickle


def test_open_in_browser():
    papis.config.set('browser', 'echo')
    papis.config.set('browse-key', 'url')
    assert(
        open_in_browser( from_data({'url': 'hello.com'}) ) ==
        'hello.com'
    )
    papis.config.set('browse-key', 'doi')
    assert( open_in_browser( from_data({'doi': '12312/1231'}) ) ==
        'https://doi.org/12312/1231'
    )
    papis.config.set('browse-key', 'nonexistentkey')
    assert(
        open_in_browser( from_data({'title': 'blih', 'author': 'me'}) ) ==
        'https://duckduckgo.com/?q=blih+me'
    )


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
