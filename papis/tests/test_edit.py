import papis.bibtex
import unittest
import papis.tests
import papis.config
from papis.commands.edit import run


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        papis.tests.setup_test_library()

    def get_docs(self):
        db = papis.database.get()
        return db.get_all_documents()

    def test_run_function_exists(self):
        self.assertTrue(run is not None)

    def test_update(self):
        docs = self.get_docs()
        doc = docs[0]
        title = doc['title'] + 'test_update'
        self.assertTrue(title is not None)

        # mocking
        doc['title'] = title
        doc.save()

        run(doc, editor='ls')
        db = papis.database.get()
        docs = db.query_dict(dict(title=title))
        self.assertTrue(len(docs) == 1)
        self.assertTrue(docs[0]['title'] == title)
