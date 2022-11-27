import tests
import unittest
import papis.config


class TestCli(unittest.TestCase):

    runner = None
    cli = None

    @classmethod
    def setUpClass(cls):
        tests.setup_test_library()

    def setUp(self):
        from click.testing import CliRunner
        self.runner = CliRunner()
        self.assertEqual(papis.config.get_lib_name(), tests.get_test_lib_name())

    def invoke(self, *args, **kwargs):
        return self.runner.invoke(self.cli, *args, **kwargs)

    def do_test_cli_function_exists(self):
        self.assertIsNot(self.cli, None)

    def do_test_help(self):
        for flag in ["-h", "--help"]:
            result = self.invoke([flag])
            self.assertNotEqual(len(result.output), 0)
