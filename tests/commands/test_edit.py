import papis.bibtex
import unittest
import tests
import papis.config
from papis.commands.edit import run, cli
import os


class TestRun(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        tests.setup_test_library()

    def get_docs(self):
        db = papis.database.get()
        return db.get_all_documents()

    def test_run_function_exists(self):
        self.assertIsNot(run, None)

    def test_update(self):
        docs = self.get_docs()
        doc = docs[0]
        title = doc["title"] + "test_update"
        self.assertIsNot(title, None)

        # mocking
        doc["title"] = title
        doc.save()

        papis.config.set("editor", "ls")
        run(doc)
        db = papis.database.get()
        docs = db.query_dict(dict(title=title))
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["title"], title)


class TestCli(tests.cli.TestCli):

    cli = cli

    def test_main(self):
        self.do_test_cli_function_exists()
        self.do_test_help()

    def test_simple(self):
        result = self.invoke([
            "krishnamurti"
        ])
        self.assertEqual(result.exit_code, 0)

    def test_doc_not_found(self):
        result = self.invoke([
            'this document it"s not going to be found'
        ])
        self.assertEqual(result.exit_code, 0)

    def test_all(self):
        result = self.invoke([
            "krishnamurti", "--all", "-e", "ls"
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(papis.config.get("editor"), "ls")

    def test_config(self):
        self.assertTrue(papis.config.get("notes-name"))

    def test_notes(self):
        result = self.invoke([
            "krishnamurti", "--all", "-e", "echo", "-n"
        ])
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(papis.config.get("editor"), "echo")

        db = papis.database.get()
        docs = db.query_dict(dict(author="Krishnamurti"))
        self.assertEqual(len(docs), 1)
        doc = docs[0]
        notespath = os.path.join(
            doc.get_main_folder(),
            papis.config.get("notes-name")
        )
        self.assertTrue(os.path.exists(notespath))
