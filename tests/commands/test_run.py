import unittest

from papis.commands.run import run
import papis.config

import tests
import tests.cli


class Test(tests.cli.TestWithLibrary):

    @classmethod
    def tearDownClass(cls):
        pass

    def test_run_ls(self) -> None:
        status = run(papis.config.get_lib_dirs()[0], command=["ls"])
        assert status == 0

    def test_run_nonexistent(self) -> None:
        status = run(papis.config.get_lib_dirs()[0], command=["nonexistent"])
        assert not status == 0
