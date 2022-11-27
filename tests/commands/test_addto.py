import unittest
import tests
import papis.config
from papis.commands.addto import run


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        tests.setup_test_library()

    def test_simple_add(self):
        db = papis.database.get()
        docs = db.query_dict({"author": "krishnamurti"})
        self.assertEqual(len(docs), 1)
        doc = docs[0]

        # add N files
        nfiles = 10
        inputfiles = [tests.create_random_pdf() for i in range(nfiles)]

        old_files = doc.get_files()

        run(doc, inputfiles)
        self.assertEqual(len(doc.get_files()), len(old_files) + nfiles)
