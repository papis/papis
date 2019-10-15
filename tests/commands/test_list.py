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
        assert(papis.config.get_lib_name() == tests.get_test_lib_name())

    def test_list_info_notes(self):
        for k in [[dict(info_files=True), 1], [dict(notes=True), 0]]:
            objs = run(papis.database.get().get_all_documents(), **k[0])
            assert(isinstance(objs, list))
            assert(len(objs) >= k[1])

    def test_list_libs(self):
        libs = run([], libraries=True)
        assert(len(libs) >= 1)

    def test_list_folders(self):
        folders = run(
           papis.database.get().get_all_documents(),
           folders=True
        )
        assert(len(folders) >= 1)
        assert(isinstance(folders, list))
        for f in folders:
            assert(os.path.exists(f))
