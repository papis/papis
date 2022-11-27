"""
import unittest
import tests
import papis.config
from papis.commands.check import run


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        tests.setup_test_library()

    def get_docs(self):
        db = papis.database.get()
        return db.get_all_documents()

    def test_simple(self):
        docs = self.get_docs()
        dds = run(["doi"], docs)
        self.assertEqual(len(dds), len(docs))

    def test_dicts(self):
        docs = self.get_docs()
        dds = run(["doi"], docs)
        self.assertEqual(len(dds[0].keys()), 3)
        self.assertIn("msg", dds[0].keys())
        self.assertIn("doc", dds[0].keys())
        self.assertIn("key", dds[0].keys())

    def test_config(self):
        keys = papis.config.get("check-keys")
        self.assertIsInstance(keys, str)
        self.assertIsNot(keys, None)
        lkeys = eval(keys)
        self.assertIsInstance(lkeys, list)

    def test_files(self):
        docs = self.get_docs()
        dds = run(["files"], docs)
        self.assertEqual(len(dds), len(docs))
"""
