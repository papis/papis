import os
import tempfile
import unittest
import papis.tests
import papis.config
from papis.commands.add import run


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        papis.tests.setup_test_library()

    def test_add_with_data(self):
        data = {
            "journal": "International Journal of Quantum Chemistry",
            "language": "en",
            "issue": "15",
            "title": "How many-body perturbation theory has changed qm ",
            "url": "http://doi.wiley.com/10.1002/qua.22384",
            "volume": "109",
            "author": "Kutzelnigg, Werner",
            "type": "article",
            "doi": "10.1002/qua.22384",
            "year": "2009",
            "ref": "2FJT2E3A"
        }
        number_of_files = 10
        paths = [
            tempfile.mktemp() for i in range(number_of_files)
        ]
        for p in paths:
            open(p, 'w+').close()
        run(
            paths,
            data=data
        )
        db = papis.database.get()
        docs = db.query_dict(dict(author="Kutzelnigg, Werner"))
        self.assertTrue(len(docs) == 1)
        doc = docs[0]
        self.assertTrue(doc is not None)
        self.assertTrue(len(doc.get_files()) == number_of_files)
