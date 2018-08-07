import os
import unittest
import papis.tests
import papis.config
from papis.commands.rm import run


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        papis.tests.setup_test_library()

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
