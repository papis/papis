import os
import sys
import pytest
import tempfile
from unittest.mock import patch

import papis.config
import papis.database
import papis.document
import papis.commands.add
from papis.utils import (
    get_cache_home, create_identifier, locate_document,
    general_open, clean_document_name,
)
from papis.filetype import get_document_extension

import tests


@pytest.mark.skipif(sys.platform != "linux", reason="uses linux paths")
def test_get_cache_home():
    os.environ["XDG_CACHE_HOME"] = '~/.cache'
    assert(
        get_cache_home() == os.path.expanduser(
            os.path.join(os.environ["XDG_CACHE_HOME"], 'papis')
        )
    )
    os.environ["XDG_CACHE_HOME"] = os.path.abspath('/tmp/.cache')
    assert(get_cache_home() == os.path.abspath('/tmp/.cache/papis'))
    assert(os.path.exists(get_cache_home()))
    del os.environ["XDG_CACHE_HOME"]
    assert (
        get_cache_home() ==
        os.path.abspath(os.path.expanduser(os.path.join('~/.cache', 'papis')))
    )
    tmp = os.path.join(tempfile.mkdtemp(), 'blah')
    papis.config.set('cache-dir', tmp)
    assert(get_cache_home() == tmp)


def test_create_identifier():
    import itertools
    import string
    output = list(
        itertools.islice(
            create_identifier(string.ascii_uppercase),
            30
        )
    )
    expected = [
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        'AA', 'AB', 'AC', 'AD'
    ]
    for i in range(30):
        assert(output[i] == expected[i])


@pytest.mark.skipif(sys.platform != "linux", reason="uses linux tools")
def test_general_open_with_spaces():
    filename = tempfile.mktemp("File with at least a couple of spaces")

    with open(filename, 'w+') as fd:
        fd.write('Some content')

    assert(os.path.exists(filename))

    general_open(
        filename,
        'nonexistentoption',
        default_opener="sed -i s/o/u/g",
        wait=True
    )

    with open(filename) as fd:
        content = fd.read()
        assert(content == 'Sume cuntent')


def test_locate_document():
    from papis.document import from_data
    docs = [
        from_data(dict(doi='10.1021/ct5004252', title='Hello world')),
        from_data(
            dict(
                doi='10.123/12afad12',
                author='noone really',
                title='Hello world'
            )
        ),
    ]

    doc = from_data(dict(doi='10.1021/CT5004252'))
    found_doc = locate_document(doc, docs)
    assert found_doc is not None

    doc = from_data(dict(doi='CT5004252'))
    found_doc = locate_document(doc, docs)
    assert found_doc is None

    doc = from_data(dict(author='noone really'))
    found_doc = locate_document(doc, docs)
    assert found_doc is None

    doc = from_data(dict(title='Hello world'))
    found_doc = locate_document(doc, docs)
    assert found_doc is None


def test_extension():
    docs = [
        [tests.create_random_pdf(), "pdf"],
        [tests.create_random_pdf(), "pdf"],
        [tests.create_random_file(), "data"],
        [tests.create_random_epub(), "epub"],
        [tests.create_random_file(suffix='.yaml'), "yaml"],
        [tests.create_random_file(suffix='.text'), "text"],
    ]
    for d in docs:
        assert(get_document_extension(d[0]) == d[1])


def test_slugify():
    assert(
        clean_document_name('{{] __ }}albert )(*& $ß $+_ einstein (*]') ==
        'albert-ss-einstein'
    )
    assert(
        clean_document_name('/ashfd/df/  #$%@#$ }{_+"[ ]hello öworld--- .pdf')
        ==
        'hello-oworld-.pdf'
    )
    assert(clean_document_name('масса и енергиа.pdf') == 'massa-i-energia.pdf')
    assert(clean_document_name('الامير الصغير.pdf') == 'lmyr-lsgyr.pdf')
