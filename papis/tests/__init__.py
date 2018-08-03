import tempfile
import papis.config
import papis.api
import papis.utils
import papis.document
import os
import unittest


test_data = [
    {"author": 'J. Krishnamurti', "title": 'Freedom from the known',
        "year": '2009'},
    {"author": 'K. Popper', "title": 'The open society', "volume": 'I'},
]


def get_test_lib():
    return 'test-lib'


def setup_test_library(save_settings_fileds=[]):
    """Set-up a test library for tests

    :param save_settings_fileds: The papis configuration will be initialized
        to some default. This argument should contain a list of keys that
        are to be kept in the configuration and not wiped out.
    :type  save_settings_fileds: list
    """
    lib = get_test_lib()
    config = papis.config.get_configuration()
    settings = papis.config.get_general_settings_name()
    settings_conf = {
        key: config['settings'][key] for key in save_settings_fileds
    }
    config[settings] = settings_conf
    config[lib] = dict()
    config[lib]['dir'] = tempfile.mkdtemp(prefix='papis')
    papis.api.set_lib('test-lib')
    papis.database.clear_cached()

    for i, data in enumerate(test_data):
        doc = papis.document.from_data(data)
        folder = os.path.join(
            papis.config.get('dir'), str(i)
        )
        os.makedirs(folder)
        doc.set_folder(folder)
        doc.save()


