import papis.bibtex
import tempfile
import unittest
import tests
import papis.config
from papis.commands.update import run, cli
import os
import re


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        tests.setup_test_library()

    def get_docs(self):
        db = papis.database.get()
        return db.get_all_documents()

    def test_data(self):
        db = papis.database.get()
        docs = self.get_docs()
        self.assertTrue(docs)
        doc = docs[0]
        data = dict()
        data['tags'] = 'test_data'
        run(doc, data=data, force=True)
        docs = db.query_dict(dict(tags='test_data'))
        self.assertTrue(docs)


class TestCli(tests.cli.TestCli):

    cli = cli

    def test_main(self):
        self.do_test_cli_function_exists()
        self.do_test_help()

    def test_set(self):
        db = papis.database.get()
        result = self.invoke([
            'krishnamurti', '--set', 'editor', 'ls', '-b', '-f'
        ])
        self.assertTrue(result.exit_code == 0)
        docs = db.query_dict(dict(author='krishnamurti'))
        self.assertTrue(docs)
        # TODO: if I don't load, it fails, why?
        docs[0].load()
        self.assertEqual(docs[0]['editor'], 'ls')

    def test_yaml(self):
        yamlpath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data', 'ken.yaml'
        )
        self.assertTrue(os.path.exists(yamlpath))

        result = self.invoke([
            'krishnamurti', '--from-yaml', yamlpath, '-b'
        ])
        db = papis.database.get()
        docs = db.query_dict(dict(author='krishnamurti'))
        self.assertTrue(docs)
        # TODO: if I don't load, it fails, why?
        docs[0].load()
        self.assertEqual('10.1143/JPSJ.44.1627', docs[0]['doi'])

    def test_bibtex_no_force_and_force(self):
        bibpath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data', 'lib1.bib'
        )
        self.assertTrue(os.path.exists(bibpath))

        result = self.invoke([
            'krishnamurti', '--from-bibtex', bibpath, '-b'
        ])
        db = papis.database.get()
        docs = db.query_dict(dict(author='krishnamurti'))
        self.assertTrue(docs)
        # TODO: if I don't load, it fails, why?
        docs[0].load()
        self.assertTrue(
            re.match(r' *10.1002/andp.19053221004 *', docs[0]['doi'])
        )
        self.assertTrue(
            re.match(r'.*Krishnamurti.*', docs[0]['author'])
        )

        result = self.invoke([
            'krishnamurti', '--from-bibtex', bibpath, '-bf', '--all'
        ])
        db = papis.database.get()
        docs = db.query_dict(dict(author='krishnamurti'))
        self.assertTrue(docs)
        # TODO: if I don't load, it fails, why?
        docs[0].load()
        self.assertTrue(
            re.match(r' *10.1002/andp.19053221004 *', docs[0]['doi'])
        )
        self.assertTrue(
            re.match(r'.*Krishnamurti.*', docs[0]['author']) is None
        )
        self.assertEqual(
            r' Zur Elektrodynamik bewegter K\"{o}rper ',
            docs[0]['title']
        )
