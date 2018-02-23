import os
import unittest
import papis.tests
import papis.config
from papis.commands.list import run


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        papis.tests.setup_test_library()

    @classmethod
    def tearDownClass(self):
        pass

    def test_lib_is_correct(self):
        assert(papis.config.get_lib() == papis.tests.get_test_lib())

    def test_list_docs(self):
        docs = run(query='', library=papis.config.get_lib())
        assert(isinstance(docs, list))
        assert(len(docs) >= 1)

    def test_list_docs_no_lib(self):
        docs = run(query='')
        assert(isinstance(docs, list))
        assert(len(docs) >= 1)

    def test_list_libs(self):
        libs = run(libraries=True)
        assert(len(libs) >= 1)
        assert(papis.config.get('dir') in libs)

    def test_list_folders(self):
        folders = run(query="", library=papis.config.get_lib(), folders=True)
        assert(len(folders) >= 1)
        assert(isinstance(folders, list))
        for f in folders:
            assert(os.path.exists(f))
