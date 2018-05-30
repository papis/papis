import tempfile
import unittest
import papis.tests
import papis.config
from papis.commands.addto import run


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        papis.tests.setup_test_library()

    def test_simple_add(self):
        db = papis.database.get()
        docs = db.get_all_documents()
        doc = docs[0]
        N = 10
        # add 10 files
        inputfiles = [tempfile.mktemp() for i in range(N)]
        for i in inputfiles:
            open(i, 'w+').close()
        self.assertTrue(len(doc.get_files()) == 1)
        run(doc, inputfiles)
        self.assertTrue(len(doc.get_files()) == 1+10)
        docs = db.get_all_documents()
        doc = docs[0]
        self.assertTrue(len(doc.get_files()) == 1+10)
