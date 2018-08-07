"""
import unittest
import tests
import papis.config
from papis.commands.check import run


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        tests.setup_test_library()

    def get_docs(self):
        db = papis.database.get()
        return db.get_all_documents()

    def test_simple(self):
        docs = self.get_docs()
        dds = run(['doi'], docs)
        self.assertTrue(len(dds) == len(docs))

    def test_dicts(self):
        docs = self.get_docs()
        dds = run(['doi'], docs)
        self.assertTrue(len(dds[0].keys()) == 3)
        self.assertTrue('msg' in dds[0].keys())
        self.assertTrue('doc' in dds[0].keys())
        self.assertTrue('key' in dds[0].keys())

    def test_config(self):
        keys = papis.config.get('check-keys')
        self.assertTrue(isinstance(keys, str))
        self.assertTrue(keys is not None)
        lkeys = eval(keys)
        self.assertTrue(isinstance(lkeys, list))

    def test_files(self):
        docs = self.get_docs()
        dds = run(['files'], docs)
        self.assertTrue(len(dds) == len(docs))
"""
