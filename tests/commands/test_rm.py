import os
import unittest
from unittest.mock import patch

import papis.config
import papis.commands.rm

import tests


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        tests.setup_test_library()

    def test_rm_document(self):
        db = papis.database.get()
        docs = db.get_all_documents()
        ndocs = len(docs)
        self.assertGreater(ndocs, 0)
        doc = docs[0]
        papis.commands.rm.run(doc)
        docs = db.get_all_documents()
        ndocs_after_delete = len(docs)
        self.assertGreater(ndocs, ndocs_after_delete)

    def test_rm_documents_file(self):
        db = papis.database.get()
        docs = db.get_all_documents()
        doc = docs[0]
        title = doc["title"]
        filename = "test.txt"
        path = os.path.join(doc.get_main_folder(), filename)

        open(path, "w+").close()
        self.assertTrue(os.path.exists(path))

        doc["files"] = [filename]
        doc.save()

        papis.commands.rm.run(doc, filepath=path)
        self.assertFalse(os.path.exists(path))

        doc = db.query_dict(dict(title=title))[0]
        self.assertIsNot(doc, None)
        self.assertEqual(doc["title"], title)
        self.assertEqual(len(doc.get_files()), 0)


class TestCli(tests.cli.TestCli):

    cli = papis.commands.rm.cli

    def test_1_no_documents(self):
        result = self.invoke(["__no_document__"])
        self.assertEqual(result.exit_code, 0)

    @patch("papis.pick.pick_doc", lambda x: [])
    def test_2_no_doc_picked(self):
        result = self.invoke(["turing"])
        self.assertEqual(result.exit_code, 0)

    def test_3_force(self):
        db = papis.database.get()
        result = self.invoke(["krishnamurti", "--force"])
        self.assertEqual(result.exit_code, 0)
        docs = db.query_dict(dict(author="krish"))
        self.assertFalse(docs)

    @patch("papis.tui.utils.text_area", lambda **y: False)
    @patch("papis.tui.utils.confirm", lambda *x, **y: False)
    @patch("papis.pick.pick_doc", lambda x: [x[0]] if x else [])
    def test_4_confirm(self):
        db = papis.database.get()
        docs = db.query_dict(dict(author="popper"))
        self.assertEqual(len(docs), 1)
        result = self.invoke(["popper"])
        self.assertEqual(result.exit_code, 0)
        docs = db.query_dict(dict(author="popper"))
        self.assertTrue(docs)

    @patch("papis.tui.utils.text_area", lambda **y: False)
    @patch("papis.tui.utils.confirm", lambda *x, **y: True)
    @patch("papis.pick.pick_doc", lambda x: [x[0]] if x else [])
    def test_5_confirm_true(self):
        db = papis.database.get()
        docs = db.query_dict(dict(author="popper"))
        self.assertEqual(len(docs), 1)
        result = self.invoke(["popper"])
        self.assertEqual(result.exit_code, 0)
        docs = db.query_dict(dict(author="popper"))
        self.assertFalse(docs)

    @patch("papis.tui.utils.confirm", lambda *x, **y: True)
    @patch("papis.pick.pick_doc", lambda x: [x[0]] if x else [])
    @patch("papis.pick.pick", lambda x: [])
    def test_7_confirm_file_nopick(self):
        db = papis.database.get()
        docs = db.query_dict(dict(author="turing"))
        self.assertEqual(len(docs), 1)
        nfiles = len(docs[0].get_files())
        self.assertGreater(nfiles, 0)

        result = self.invoke(["turing", "--file"])
        self.assertEqual(result.exit_code, 0)

        docs = db.query_dict(dict(author="turing"))
        self.assertEqual(len(docs), 1)
        nfiles_after = len(docs[0].get_files())
        self.assertEqual(nfiles, nfiles_after)

    @patch("papis.tui.utils.confirm", lambda *x, **y: False)
    @patch("papis.pick.pick_doc", lambda x: [x[0]] if x else [])
    @patch("papis.pick.pick", lambda x: [x[0]] if x else [])
    def test_6_confirm_file(self):
        db = papis.database.get()
        docs = db.query_dict(dict(author="turing"))
        self.assertEqual(len(docs), 1)
        nfiles = len(docs[0].get_files())
        self.assertGreater(nfiles, 0)

        result = self.invoke(["turing", "--file"])
        self.assertEqual(result.exit_code, 0)

        docs = db.query_dict(dict(author="turing"))
        self.assertEqual(len(docs), 1)
        nfiles_after = len(docs[0].get_files())
        self.assertEqual(nfiles, nfiles_after)

    @patch("papis.tui.utils.confirm", lambda *x, **y: True)
    @patch("papis.pick.pick_doc", lambda x: [x[0]] if x else [])
    @patch("papis.pick.pick", lambda x: [x[0]] if x else [])
    def test_confirm_true_file(self):
        db = papis.database.get()
        docs = db.query_dict(dict(author="turing"))
        self.assertEqual(len(docs), 1)
        nfiles = len(docs[0].get_files())
        self.assertGreater(nfiles, 0)

        result = self.invoke(["turing", "--file"])
        self.assertEqual(result.exit_code, 0)

        docs = db.query_dict(dict(author="turing"))
        self.assertEqual(len(docs), 1)
        nfiles_after = len(docs[0].get_files())
        self.assertEqual(nfiles, nfiles_after + 1)

    def test_rm_all(self):
        db = papis.database.get()
        docs = db.query_dict(dict(author="test_author"))
        self.assertEqual(len(docs), 2)

        result = self.invoke(["test_author", "--all", "--force"])
        self.assertEqual(result.exit_code, 0)

        docs = db.query_dict(dict(author="test_author"))
        self.assertEqual(len(docs), 0)
