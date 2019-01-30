import tempfile
import papis.config
import papis.api
import papis.utils
import papis.document
import os
import shutil


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
    },
    {
        "author": 'K. Popper',
        'doi':'10.1021/ct5004252',
        "title": 'The open society',
        "volume": 'I',
        "_test_files": 0,
    },
]


def get_test_lib():
    return 'test-lib'


def setup_test_library():
    """Set-up a test library for tests

    :param save_settings_fileds: The papis configuration will be initialized
        to some default. This argument should contain a list of keys that
        are to be kept in the configuration and not wiped out.
    :type  save_settings_fileds: list
    """
    lib = get_test_lib()
    config = papis.config.get_configuration()
    config['settings'] = dict()
    config[lib] = dict()
    config[lib]['dir'] = tempfile.mkdtemp(prefix='papis')
    papis.api.set_lib(lib)
    papis.database.clear_cached()


    for i, data in enumerate(test_data):
        data['files'] = [
            create_random_pdf() for i in range(data.get('_test_files'))
        ]
        doc = papis.document.from_data(data)
        folder = os.path.join(
            papis.config.get('dir'), str(i)
        )
        os.makedirs(folder)
        doc.set_folder(folder)
        doc['files'] = [os.path.basename(f) for f in data['files']]
        doc.save()
        for f in data['files']:
            shutil.move(
                f,
                doc.get_main_folder()
            )
