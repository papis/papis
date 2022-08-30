import unittest

import papis.bibtex
import papis.config
import papis.document
import papis.commands.open

import tests
import tests.cli


class TestRun(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        tests.setup_test_library()

    def get_docs(self):
        db = papis.database.get()
        return db.get_all_documents()


class TestCli(tests.cli.TestCli):

    cli = papis.commands.open.cli

    def test_main(self):
        self.do_test_cli_function_exists()
        self.do_test_help()

    def test_tool(self):
        result = self.invoke([
            "doc without files"
        ])
        self.assertTrue(result.exit_code == 0)

        result = self.invoke([
            "Krishnamurti",
            "--tool", "nonexistingcommand"
        ])
        self.assertTrue(result.exit_code != 0)

        result = self.invoke([
            "Krishnamurti",
            "--tool", "nonexistingcommand", "--folder"
        ])
        self.assertTrue(result.exit_code != 0)

        result = self.invoke([
            "Krishnamurti", "--mark", "--all", "--tool", "dir"
        ])
        # self.assertTrue(result.exit_code == 0)
