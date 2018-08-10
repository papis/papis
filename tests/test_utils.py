import os
import tempfile
import papis.utils
import papis.config
import tests
import papis.commands.add
import papis.database
from papis.document import from_data


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
        default_opener="echo 'hello world' >> ",
        wait=True
    )

    with open(filename) as fd:
        content = fd.read()
        assert(content == 'Some contenthello world\n')


def test_locate_document():

    db = papis.database.get()

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


def test_guess_file_extension():
    from papis.utils import guess_file_extension
    assert 'pdf' == guess_file_extension('path/to/123adqfdsf/file.pdf')
    assert 'txt' == guess_file_extension('path/to/123adqfdsf/file')
    assert 'epub' == guess_file_extension('path/to/123adqfdsf/file.epub')
    assert 'djvu' == guess_file_extension('path/to/123adqfdsf/file.djvu')
    assert 'mobi' == guess_file_extension('path/to/123adqfdsf/file.mobi')
