import unittest
import os

import papis.config
import papis.bibtex
from papis.commands.update import run, cli

import tests


def _get_resource_file(filename):
    resources = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "resources", "commands", "update"
    )
    filepath = os.path.join(resources, filename)
    assert os.path.exists(filepath)

    return filepath


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        tests.setup_test_library()

    def get_docs(self):
        db = papis.database.get()
        return db.get_all_documents()

    def test_data(self):
        db = papis.database.get()
        docs = self.get_docs()
        self.assertTrue(docs)
        doc = docs[0]
        data = dict()
        data["tags"] = "test_data"
        run(doc, data=data)
        docs = db.query_dict(dict(tags="test_data"))
        self.assertTrue(docs)


class TestCli(tests.cli.TestCli):

    cli = cli

    def test_1_no_documents(self):
        result = self.invoke(["__no_document__"])
        self.assertTrue(result.exit_code == 0)

    def test_1_main(self):
        self.do_test_cli_function_exists()
        self.do_test_help()

    def test_3_set(self):
        db = papis.database.get()
        result = self.invoke([
            "krishnamurti",
            "-s", "isbn", "92130123",
            "--set", "doi", "10.213.phys.rev/213",
        ])
        self.assertTrue(result.exit_code == 0)
        docs = db.query_dict(dict(author="krishnamurti"))
        self.assertTrue(docs)
        self.assertEqual(docs[0]["doi"], "10.213.phys.rev/213")
        self.assertEqual(docs[0]["isbn"], "92130123")

    def test_7_delete_key_confirm(self):
        db = papis.database.get()
        result = self.invoke([
            "krishnamurti",
            "-s", "doi", "",
            "--set", "isbn", "",
        ])
        self.assertTrue(result is not None)
        # self.assertTrue(result.exit_code == 0)

        docs = db.query_dict(dict(author="krishnamurti"))
        self.assertTrue(len(docs) == 1)
        self.assertTrue(docs[0].has("doi"))
        self.assertTrue(docs[0].has("isbn"))
        self.assertTrue(not docs[0].get("doi"))
        self.assertTrue(not docs[0].get("isbn"))

    # def test_8_yaml(self):
    #     yamlpath = _get_resource_file("russell.yaml")
    #     result = self.invoke([
    #         "krishnamurti", "--from", "yaml", yamlpath])
    #     self.assertTrue(result is not None)

    #     db = papis.database.get()
    #     docs = db.query_dict(dict(author="krishnamurti"))
    #     self.assertTrue(docs)
    #     self.assertEqual("10.2307/2021897", docs[0]["doi"])

    # def test_9_bibtex(self):
    #     db = papis.database.get()
    #     bibpath = _get_resource_file("wannier.bib")
    #     result = self.invoke(["krishnamurti", "--from", "bibtex", bibpath])
    #     self.assertTrue(result.exit_code == 0)
    #     docs = db.query_dict(dict(author="krishnamurti"))
    #     self.assertTrue(docs)
    #     self.assertTrue(re.match(r".*Krishnamurti.*", docs[0]["author"]))

    # def test_9_bibtexerrored(self):
    #     yamlpath = _get_resource_file("russell.yaml")
    #     result = self.invoke([
    #         "krishnamurti", "--from", "bibtex", yamlpath
    #     ])
    #     self.assertTrue(result.exit_code == 0)
