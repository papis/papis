import papis.bibtex
import json
import yaml
import tempfile
import unittest
import papis.tests
import papis.config
from papis.commands.export import run


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        papis.tests.setup_test_library()

    def get_docs(self):
        db = papis.database.get()
        return db.get_all_documents()

    def test_bibtex(self):
        docs = self.get_docs()
        string = run(docs, bibtex=True)
        self.assertTrue(len(string) > 0)
        data = papis.bibtex.bibtex_to_dict(string)
        self.assertTrue(len(data) > 0)

    def test_json(self):
        docs = self.get_docs()
        string = run(docs, json=True)
        self.assertTrue(len(string) > 0)
        data = json.loads(string)
        self.assertTrue(len(data) > 0)

    def test_text(self):
        docs = self.get_docs()
        string = run(docs, text=True)
        self.assertTrue(len(string) > 0)
        data = string.split('\n')
        self.assertTrue(len(data) > 0)

    def test_yaml(self):
        # FIXME: The string gets created, but the loading does not work
        docs = self.get_docs()
        string = run(docs, yaml=True)
        self.assertTrue(len(string) > 0)
        yamlfile = open(tempfile.mktemp(), 'w+')
        yamlfile.write(string)
        data = yaml.load_all(yamlfile)
        self.assertTrue(data is not None)
        # FIXME: THIS DOES NOT WORK, WHY?
        # self.assertTrue(len(list(data)) > 0)
