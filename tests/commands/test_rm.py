import os
import unittest
from unittest.mock import patch
import tests
import papis.config
from papis.commands.rm import run, cli


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        tests.setup_test_library()

    def test_rm_document(self):
        db = papis.database.get()
        docs = db.get_all_documents()
        Ni = len(docs)
        self.assertTrue(Ni > 0)
        doc = docs[0]
        run(doc)
        docs = db.get_all_documents()
        Nf = len(docs)
        self.assertTrue(Ni - Nf > 0)

    def test_rm_documents_file(self):
        db = papis.database.get()
        docs = db.get_all_documents()
        doc = docs[0]
        title = doc['title']
        filename = 'test.txt'
        path = os.path.join(doc.get_main_folder(), filename)

        open(path, 'w+').close()
        self.assertTrue(os.path.exists(path))

        doc['files'] = [filename]
        doc.save()

        run(doc, filepath=path)
        self.assertTrue(not os.path.exists(path))

        doc = db.query_dict(dict(title=title))[0]
        self.assertTrue(doc is not None)
        self.assertTrue(doc['title'] == title)
        self.assertTrue(len(doc.get_files()) == 0)


class TestCli(tests.cli.TestCli):

    cli = cli

    def test_1_no_documents(self):
        result = self.invoke(['__no_document__'])
        self.assertTrue(result.exit_code == 0)

    @patch('papis.pick.pick_doc', lambda x: None)
    def test_2_no_doc_picked(self):
        result = self.invoke(['turing'])
        self.assertTrue(result.exit_code == 0)

    def test_3_force(self):
        db = papis.database.get()
        result = self.invoke(['krishnamurti', '--force'])
        self.assertTrue(result.exit_code == 0)
        docs = db.query_dict(dict(author='krish'))
        self.assertFalse(docs)

    @patch('papis.utils.text_area', lambda **y: False)
    @patch('papis.utils.confirm', lambda *x, **y: False)
    @patch('papis.pick.pick_doc', lambda x: x[0] if x else None)
    def test_4_confirm(self):
        db = papis.database.get()
        docs = db.query_dict(dict(author='popper'))
        self.assertTrue(len(docs) == 1)
        result = self.invoke(['popper'])
        self.assertTrue(result.exit_code == 0)
        docs = db.query_dict(dict(author='popper'))
        self.assertTrue(docs)

    @patch('papis.utils.text_area', lambda **y: False)
    @patch('papis.utils.confirm', lambda *x, **y: True)
    @patch('papis.pick.pick_doc', lambda x: x[0] if x else None)
    def test_5_confirm_true(self):
        db = papis.database.get()
        docs = db.query_dict(dict(author='popper'))
        self.assertTrue(len(docs) == 1)
        result = self.invoke(['popper'])
        self.assertTrue(result.exit_code == 0)
        docs = db.query_dict(dict(author='popper'))
        self.assertFalse(docs)

    @patch('papis.utils.confirm', lambda *x, **y: True)
    @patch('papis.pick.pick_doc', lambda x: x[0] if x else None)
    @patch('papis.pick.pick', lambda x: None)
    def test_7_confirm_file_nopick(self):
        db = papis.database.get()
        docs = db.query_dict(dict(author='turing'))
        self.assertTrue(len(docs) == 1)
        N = len(docs[0].get_files())
        self.assertTrue(N > 0)

        result = self.invoke(['turing', '--file'])
        self.assertTrue(result.exit_code == 0)

        docs = db.query_dict(dict(author='turing'))
        self.assertTrue(len(docs) == 1)
        Nf = len(docs[0].get_files())
        self.assertTrue(N == Nf)

    @patch('papis.utils.confirm', lambda *x, **y: False)
    @patch('papis.pick.pick_doc', lambda x: x[0] if x else None)
    @patch('papis.pick.pick', lambda x: x[0] if x else None)
    def test_6_confirm_file(self):
        db = papis.database.get()
        docs = db.query_dict(dict(author='turing'))
        self.assertTrue(len(docs) == 1)
        N = len(docs[0].get_files())
        self.assertTrue(N > 0)

        result = self.invoke(['turing', '--file'])
        self.assertTrue(result.exit_code == 0)

        docs = db.query_dict(dict(author='turing'))
        self.assertTrue(len(docs) == 1)
        Nf = len(docs[0].get_files())
        self.assertTrue(N == Nf)


    @patch('papis.utils.confirm', lambda *x, **y: True)
    @patch('papis.pick.pick_doc', lambda x: x[0] if x else None)
    @patch('papis.pick.pick', lambda x: x[0] if x else None)
    def test_confirm_true_file(self):
        db = papis.database.get()
        docs = db.query_dict(dict(author='turing'))
        self.assertTrue(len(docs) == 1)
        N = len(docs[0].get_files())
        self.assertTrue(N > 0)

        result = self.invoke(['turing', '--file'])
        self.assertTrue(result.exit_code == 0)

        docs = db.query_dict(dict(author='turing'))
        self.assertTrue(len(docs) == 1)
        Nf = len(docs[0].get_files())
        self.assertTrue(N == Nf+1)
