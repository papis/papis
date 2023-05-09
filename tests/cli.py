import unittest
from typing import Any, Optional

import click
import click.testing

import papis.config

import tests


class TestWithLibrary(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        tests.setup_test_library()


class TestCli(TestWithLibrary):

    runner: Optional[click.testing.CliRunner] = None
    cli: Optional[click.BaseCommand] = None

    def setUp(self) -> None:
        self.runner = click.testing.CliRunner()
        self.assertEqual(papis.config.get_lib_name(),
                         tests.get_test_lib_name())

    def invoke(self, *args: Any, **kwargs: Any) -> click.testing.Result:
        if self.runner is not None and self.cli is not None:
            return self.runner.invoke(self.cli, *args, **kwargs)
        raise RuntimeError("Runner or cli are not set")

    def do_test_cli_function_exists(self) -> None:
        self.assertIsNot(self.cli, None)

    def do_test_help(self) -> None:
        for flag in ["-h", "--help"]:
            result = self.invoke([flag])
            self.assertNotEqual(len(result.output), 0)
