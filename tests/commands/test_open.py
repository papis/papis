import papis.bibtex
import json
import yaml
import tempfile
import unittest
import tests
import tests.cli
import papis.config
import papis.document
from papis.commands.open import run, cli
import re
import os


class TestRun(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        tests.setup_test_library()

    def get_docs(self):
        db = papis.database.get()
        return db.get_all_documents()


class TestCli(tests.cli.TestCli):

    cli = cli

    def test_main(self):
        self.do_test_cli_function_exists()
        self.do_test_help()

    def test_tool(self):
        result = self.invoke([
            'doc without files'
        ])
        self.assertTrue(result.exit_code == 0)

        result = self.invoke([
            'Krishnamurti',
            '--tool', 'nonexistingcommand'
        ])
        self.assertTrue(result.exit_code != 0)

        result = self.invoke([
            'Krishnamurti',
            '--tool', 'nonexistingcommand', '--folder'
        ])
        self.assertTrue(result.exit_code != 0)

        result = self.invoke([
            'Krishnamurti', '--mark', '--all', '--tool', 'dir'
        ])
        # self.assertTrue(result.exit_code == 0)
