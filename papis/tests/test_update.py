import papis.bibtex
import tempfile
import unittest
import papis.tests
import papis.config
from papis.commands.update import run


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        papis.tests.setup_test_library()

    def get_docs(self):
        db = papis.database.get()
        return db.get_all_documents()

    def test_bibtex(self):
        db = papis.database.get()
        bibstring = """
        @article{10.1002/andp.19053221004,
          author = { A. Einstein },
          doi = { 10.1002/andp.19053221004 },
          issue = { 10 },
          journal = { Ann. Phys. },
          pages = { 891--921 },
          title = { Zur Elektrodynamik bewegter K\"{o}rper },
          type = { article },
          volume = { 322 },
          year = { 1905 },
        }

        @article{10.1002/andp.19053221004,
          author = { Perico de los palotes },
          doi = { 10.1002/andp.19053221004 },
          issue = { 10 },
          journal = { Ann. Phys. },
          pages = { 891--921 },
          title = { La biblia en HD },
          type = { article },
          volume = {322},
          year = { 1905 },
        }
        """
        bibfile = tempfile.mktemp()
        with open(bibfile, 'w+') as fd:
            fd.write(bibstring)

        docs = self.get_docs()
        run(docs[0], from_bibtex=bibfile)
        docs = db.query_dict(dict(title='elektrodynamik'))
        self.assertTrue(len(docs) == 0)

        docs = self.get_docs()
        run(docs[0], force=True, from_bibtex=bibfile)
        docs = db.query_dict(dict(title='elektrodynamik'))
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["volume"], "322")
