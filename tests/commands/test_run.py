import unittest
import tests
from papis.commands.run import run
import papis.config


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        tests.setup_test_library()

    @classmethod
    def tearDownClass(self):
        pass

    def test_run_ls(self):
        status = run(papis.config.get_lib_dirs()[0], command=['ls'])
        assert(status == 0)

    def test_run_nonexistent(self):
        status = run(papis.config.get_lib_dirs()[0], command=['nonexistent'])
        assert(not status == 1)
