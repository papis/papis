import papis.bibtex
import unittest
import tests
import papis.config
from papis.commands.browse import run


# TODO: Implement meaningful tests
class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        tests.setup_test_library()

    def test_get_docs(self):
        db = papis.database.get()
        docs = db.get_all_documents()
        self.assertTrue(len(docs) > 0)
        return docs

    def test_run_function_exists(self):
        self.assertTrue(run is not None)
