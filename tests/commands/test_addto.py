import tempfile
import unittest
import tests
import papis.config
from papis.commands.addto import run


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        tests.setup_test_library()

    def test_simple_add(self):
        db = papis.database.get()
        docs = db.query_dict({'author': 'krishnamurti'})
        assert(len(docs) == 1)
        doc = docs[0]

        # add N files
        N = 10
        inputfiles = [tests.create_random_pdf() for i in range(N)]

        old_files = doc.get_files()

        run(doc, inputfiles)
        self.assertTrue(len(doc.get_files()) == len(old_files) + N)

