import tempfile
import papis.config
import papis.api
import papis.utils
import papis.document
import papis.library
from papis.downloaders.base import Downloader
import os
import shutil


class MockDownloader(Downloader):
    def __init__(self, url="", name="", bibtex_data=None, document_data=None):
        self.bibtex_data = bibtex_data
        self.document_data = document_data


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


def create_real_document(data, suffix=''):
    folder = tempfile.mkdtemp(suffix=suffix)
    doc = papis.document.Document(folder=folder, data=data)
    doc.save()
    assert(os.path.exists(doc.get_info_file()))
    return doc


test_data = [
    {
        "author": 'doc without files',
        "title": 'Title of doc without files',
        "year": '1093',
        "_test_files": 0,
    },
    {
        "author": 'J. Krishnamurti',
        "title": 'Freedom from the known',
        "year": '2009',
        "_test_files": 1,
    }, {
        "author": 'K. Popper',
        'doi': '10.1021/ct5004252',
        "title": 'The open society',
        "volume": 'I',
        "_test_files": 0,
    }, {
        "author": "Turing A. M.",
        "doi": "10.1112/plms/s2-42.1.230",
        "issue": "1",
        "journal": "Proceedings of the London Mathematical Society",
        "note": "First turing machine paper foundation of cs",
        "pages": "230--265",
        "title": "On Computable Numbers with an Application to the Entscheidungsproblem",
        "url": "https://api.wiley.com/onlinelibrary/tdm/v1/articles/10.1112%2Fplms%2Fs2-42.1.230",
        "volume": "s2-42",
        "year": "1937",
        "_test_files": 2,
    }
]


def get_test_lib_name():
    return 'test-lib'


def setup_test_library():
    """Set-up a test library for tests
    """
    config = papis.config.get_configuration()
    config['settings'] = dict()
    folder = tempfile.mkdtemp(prefix='papis-test-library-')
    libname = get_test_lib_name()
    lib = papis.library.Library(libname, [folder])
    papis.config.set_lib(lib)
    papis.database.clear_cached()
    os.environ['XDG_CACHE_HOME'] = tempfile.mkdtemp(
        prefix='papis-test-cache-home-'
    )

    for i, data in enumerate(test_data):
        data['files'] = [
            create_random_pdf() for i in range(data.get('_test_files'))
        ]
        doc = papis.document.from_data(data)
        folder = os.path.join(papis.config.get_lib().paths[0], str(i))
        os.makedirs(folder)
        assert(os.path.exists(folder))
        doc.set_folder(folder)
        doc['files'] = [os.path.basename(f) for f in data['files']]
        doc.save()
        for f in data['files']:
            shutil.move(
                f,
                doc.get_main_folder()
            )
        assert(os.path.exists(doc.get_main_folder()))
        assert(os.path.exists(doc.get_info_file()))
