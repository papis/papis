import os
import tempfile
import papis.utils
import papis.config
import tests
import papis.commands.add
import papis.database
from papis.document import from_data
from papis.utils import (
    get_document_extension,
    clean_document_name
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
