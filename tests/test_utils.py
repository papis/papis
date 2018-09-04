import os
import tempfile
import papis.utils
import papis.config
import tests
import papis.commands.add
import papis.database
from papis.document import from_data
from papis.utils import (
    get_document_extension
)


def test_create_identifier():
    import itertools
    import string
    output = list(
        itertools.islice(
            papis.utils.create_identifier(string.ascii_uppercase),
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


def test_general_open_with_spaces():
    filename = tempfile.mktemp("File with at least a couple of spaces")

    with open(filename, 'w+') as fd:
        fd.write('Some content')

    assert(os.path.exists(filename))

    papis.utils.general_open(
        filename,
        'nonexistentoption',
        default_opener="sed -i s/o/u/g",
        wait=True
    )

    with open(filename) as fd:
        content = fd.read()
        assert(content == 'Sume cuntent')


def test_locate_document():

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
    found_doc = papis.utils.locate_document(doc, docs)
    assert found_doc is not None

    doc = from_data(dict(doi='CT5004252'))
    found_doc = papis.utils.locate_document(doc, docs)
    assert found_doc is None

    doc = from_data(dict(author='noone really'))
    found_doc = papis.utils.locate_document(doc, docs)
    assert found_doc is None

    doc = from_data(dict(title='Hello world'))
    found_doc = papis.utils.locate_document(doc, docs)
    assert found_doc is None


def test_format_doc():
    import papis.document
    from papis.utils import format_doc
    import tests
    tests.setup_test_library()
    document = from_data(dict(author='Fulano', title='Something'))

    papis.config.set('format-jinja2-enable', True)
    assert format_doc('{{doc["author"]}}{{doc["title"]}}', document) == \
        'FulanoSomething'
    assert format_doc(
        '{{doc["author"]}}{{doc["title"]}}{{doc["blahblah"]}}', document
    ) == 'FulanoSomething'

    papis.config.set('format-jinja2-enable', False)
    assert format_doc('{doc[author]}{doc[title]}', document) == \
        'FulanoSomething'
    assert format_doc('{doc[author]}{doc[title]}{doc[blahblah]}', document) ==\
        'FulanoSomething'


def create_random_pdf(suffix='', prefix=''):
    tempf = tempfile.mktemp(suffix=suffix, prefix=prefix)
    with open(tempf, 'wb+') as fd:
        fd.write('%PDF-1.5%\n'.encode())
    return tempf


def create_random_epub(suffix='', prefix=''):
    tempf = tempfile.mktemp(suffix=suffix, prefix=prefix)
    buf = [0x50, 0x4B, 0x3, 0x4]
    buf += [0x00 for i in range(26)]
    buf += [0x6D, 0x69, 0x6D, 0x65, 0x74, 0x79, 0x70, 0x65, 0x61, 0x70,
            0x70, 0x6C, 0x69, 0x63, 0x61, 0x74, 0x69, 0x6F, 0x6E, 0x2F,
            0x65, 0x70, 0x75, 0x62, 0x2B, 0x7A, 0x69, 0x70]
    buf += [0x00 for i in range(1)]
    with open(tempf, 'wb+') as fd:
        fd.write(bytearray(buf))
    return tempf


def create_random_file(suffix='', prefix=''):
    tempf = tempfile.mktemp(suffix=suffix, prefix=prefix)
    with open(tempf, 'wb+') as fd:
        fd.write('hello'.encode())
    return tempf


def test_extension():
    docs = [
        [create_random_pdf(), "pdf"],
        [create_random_pdf(), "pdf"],
        [create_random_file(), "data"],
        [create_random_epub(), "epub"],
        [create_random_file(suffix='.yaml'), "yaml"],
        [create_random_file(suffix='.text'), "text"],
    ]
    for d in docs:
        assert(get_document_extension(d[0]) == d[1])
