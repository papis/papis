import os
import unittest
import tests
import tempfile
import papis.database
from papis.commands.mv import run


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        tests.setup_test_library()

    def get_docs(self):
        db = papis.database.get()
        return db.get_all_documents()

    def test_simple_update(self):
        docs = self.get_docs()
        document = docs[0]
        title = document['title']
        new_dir = tempfile.mkdtemp()
        self.assertTrue(os.path.exists(new_dir))
        run(document, new_dir)
        docs = papis.database.get().query_dict(dict(title=title))
        self.assertTrue(len(docs) == 1)
        self.assertEqual(os.path.dirname(docs[0].get_main_folder()), new_dir)
        self.assertEqual(
            docs[0].get_main_folder(),
            os.path.join(new_dir, os.path.basename(docs[0].get_main_folder()))
        )
