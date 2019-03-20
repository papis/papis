import os
import unittest
import tests
import papis.config
import papis.database
from papis.commands.list import run


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        tests.setup_test_library()

    @classmethod
    def tearDownClass(self):
        pass

    def test_lib_is_correct(self):
        assert(papis.config.get_lib_name() == tests.get_test_lib())

    def test_list_docs(self):
        docs = run(
            query=papis.database.get_all_query_string(),
            library=papis.config.get_lib_name()
        )
        assert(isinstance(docs, list))
        assert(len(docs) >= 1)

    def test_list_docs_no_lib(self):
        docs = run(
            query=papis.database.get_all_query_string()
        )
        assert(isinstance(docs, list))
        assert(len(docs) >= 1)

    def test_list_libs(self):
        libs = run(libraries=True)
        assert(len(libs) >= 1)
        assert(papis.config.get('dir') in libs)

    def test_list_folders(self):
        folders = run(
            query=papis.database.get_all_query_string(),
            library=papis.config.get_lib_name(),
            folders=True
        )
        assert(len(folders) >= 1)
        assert(isinstance(folders, list))
        for f in folders:
            assert(os.path.exists(f))
