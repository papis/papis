import papis.tests
import unittest
import papis.config


class TestCli(unittest.TestCase):

    runner = None
    cli = None

    @classmethod
    def setUpClass(self):
        papis.tests.setup_test_library()

    def setUp(self):
        from click.testing import CliRunner
        self.runner = CliRunner()
        self.assertTrue(papis.config.get_lib() == papis.tests.get_test_lib())

    def invoke(self, *args, **kwargs):
        return self.runner.invoke(self.cli, *args, **kwargs)

    def test_cli_function_exists(self):
        self.assertTrue(self.cli is not None)

    def test_help(self):
        for flag in ['-h', '--help']:
            result = self.invoke([flag])
            self.assertFalse(len(result.output) == 0)
