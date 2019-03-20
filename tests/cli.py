import tests
import unittest
import papis.config


class TestCli(unittest.TestCase):

    runner = None
    cli = None

    @classmethod
    def setUpClass(self):
        tests.setup_test_library()

    def setUp(self):
        from click.testing import CliRunner
        self.runner = CliRunner()
        self.assertTrue(papis.config.get_lib_name() == tests.get_test_lib())

    def invoke(self, *args, **kwargs):
        return self.runner.invoke(self.cli, *args, **kwargs)

    def do_test_cli_function_exists(self):
        self.assertTrue(self.cli is not None)

    def do_test_help(self):
        for flag in ['-h', '--help']:
            result = self.invoke([flag])
            self.assertFalse(len(result.output) == 0)
