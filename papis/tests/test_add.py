import os
import tempfile
import unittest
import papis.tests
import papis.tests.cli
import papis.config
from papis.commands.add import run, get_document_extension, cli


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        papis.tests.setup_test_library()

    def test_nofile_exception(self):
        path = tempfile.mktemp()
        self.assertTrue(not os.path.exists(path))
        try:
            run(
                [path],
                data=dict(author='Bohm', title='My effect')
            )
            self.assertTrue(False)
        except IOError:
            self.assertTrue(True)

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

    def test_with_bibtex(self):
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
        """
        bibfile = tempfile.mktemp()
        with open(bibfile, 'w+') as fd:
            fd.write(bibstring)
        run(
            [bibfile],
            from_bibtex=bibfile
        )
        db = papis.database.get()
        docs = db.query_dict(
            dict(
                author="einstein",
                title="Elektrodynamik bewegter"
            )
        )
        self.assertTrue(len(docs) == 1)
        doc = docs[0]
        self.assertTrue(doc is not None)
        self.assertTrue(len(doc.get_files()) == 1)

    def test_extension(self):
        docs = [
            ["blahblah.pdf", "pdf"],
            ["b.lahblah.pdf", "pdf"],
            ["no/extension/blahblah", "txt"],
            ["a/asdfsdf21/blahblah.epub", "epub"],
        ]
        for d in docs:
            self.assertTrue(get_document_extension(d[0]) == d[1])


class TestCli(papis.tests.cli.TestCli):

    cli = cli

    def test_set(self):
        result = self.invoke([
            '--no-document',
            '-s', 'author', 'Bertrand Russell',
            '--set', 'title', 'Principia'
        ])
        self.assertTrue(result.exit_code == 0)
        db = papis.database.get()
        docs = db.query_dict(dict(author="Bertrand Russell"))
        self.assertTrue(len(docs) == 1)
