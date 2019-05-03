import papis.bibtex
import tempfile
import unittest
import tests
from unittest.mock import patch
import papis.config
from papis.commands.update import run, cli
import os
import re


def _get_resource_file(filename):
    resources = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'resources', 'commands', 'update'
    )
    filepath = os.path.join(resources, filename)
    assert(os.path.exists(filepath))
    return filepath


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

    def test_1_no_documents(self):
        result = self.invoke(['__no_document__'])
        self.assertTrue(result.exit_code == 0)

    def test_1_main(self):
        self.do_test_cli_function_exists()
        self.do_test_help()

    def test_2_set_batch_force(self):
        db = papis.database.get()
        result = self.invoke([
            'krishnamurti', '--set', 'doi', '1293.123/123', '-b', '-f'
        ])
        self.assertTrue(result.exit_code == 0)
        docs = db.query_dict(dict(author='krishnamurti'))
        self.assertTrue(docs)
        self.assertEqual(docs[0]['doi'], '1293.123/123')

    def test_3_set_batch_no_force(self):
        db = papis.database.get()
        result = self.invoke([
            'krishnamurti',
            '-s', 'isbn', '92130123',
            '--set', 'doi', '10.213.phys.rev/213',
            '-b'
        ])
        self.assertTrue(result.exit_code == 0)
        docs = db.query_dict(dict(author='krishnamurti'))
        self.assertTrue(docs)
        self.assertEqual(docs[0]['doi'], '1293.123/123')
        self.assertEqual(docs[0]['isbn'], '92130123')

    @patch('papis.utils.confirm', lambda *x, **y: False)
    def test_4_set_no_batch_no_force_no_confirm(self):
        db = papis.database.get()
        result = self.invoke([
            'krishnamurti',
            '-s', 'isbn', '00000000',
            '--set', 'doi', '10.213.phys.rev/213',
        ])
        self.assertTrue(result.exit_code == 0)
        docs = db.query_dict(dict(author='krishnamurti'))
        self.assertTrue(docs)
        self.assertEqual(docs[0]['doi'], '1293.123/123')
        self.assertEqual(docs[0]['isbn'], '92130123')

    @patch('papis.utils.confirm', lambda *x, **y: True)
    def test_5_set_no_batch_no_force_confirm(self):
        db = papis.database.get()
        result = self.invoke([
            'krishnamurti',
            '-s', 'isbn', '00000000',
            '--set', 'doi', '10.213.phys.rev/213', '-i'
        ])
        self.assertTrue(result.exit_code == 0)
        docs = db.query_dict(dict(author='krishnamurti'))
        self.assertTrue(docs)
        self.assertEqual(docs[0]['doi'], '10.213.phys.rev/213')
        self.assertEqual(docs[0]['isbn'], '00000000')

    @patch('papis.utils.confirm', lambda *x, **y: False)
    def test_6_delete_key_no_confirm(self):
        db = papis.database.get()
        docs = db.query_dict(dict(author='krishnamurti'))
        self.assertEqual(docs[0]['isbn'], '00000000')
        self.assertTrue('doi' in docs[0].keys())
        self.assertTrue('isbn' in docs[0].keys())
        result = self.invoke([
            'krishnamurti',
            '-d', 'isbn',
            '--delete', 'doi',
            '--delete', '_non_existent_key',
        ])
        self.assertTrue(result.exit_code == 0)
        docs = db.query_dict(dict(author='krishnamurti'))
        self.assertTrue(docs)
        self.assertTrue(docs[0].has('isbn'))
        self.assertTrue(docs[0].has('doi'))

    @patch('papis.utils.confirm', lambda *x, **y: True)
    def test_7_delete_key_confirm(self):
        db = papis.database.get()
        result = self.invoke([
            'krishnamurti',
            '-d', 'doi',
            '--delete', 'isbn',
            '--delete', '_non_existent_key',
        ])
        #self.assertTrue(result.exit_code == 0)
        docs = db.query_dict(dict(author='krishnamurti'))
        self.assertTrue(len(docs) == 1)
        self.assertTrue(not docs[0].has('doi'))
        self.assertTrue(not docs[0].has('isbn'))

    def test_8_yaml_no_force(self):
        yamlpath = _get_resource_file('russell.yaml')
        result = self.invoke([
            'krishnamurti', '--from-yaml', yamlpath, '-b'
        ])
        db = papis.database.get()
        docs = db.query_dict(dict(author='krishnamurti'))
        self.assertTrue(docs)
        self.assertEqual('10.2307/2021897', docs[0]['doi'])

    def test_9_bibtex_batch(self):
        db = papis.database.get()
        bibpath = _get_resource_file('wannier.bib')
        result = self.invoke([
            'krishnamurti', '--from-bibtex', bibpath, '-b'
        ])
        self.assertTrue(result.exit_code == 0)
        docs = db.query_dict(dict(author='krishnamurti'))
        self.assertTrue(docs)
        self.assertTrue(
            re.match(r'.*Krishnamurti.*', docs[0]['author'])
        )

    def test_9_bibtex_batch_errored(self):
        yamlpath = _get_resource_file('russell.yaml')
        result = self.invoke([
            'krishnamurti', '--from-bibtex', yamlpath, '-b'
        ])
        self.assertTrue(result.exit_code == 0)

    # def test_5_bibtex_force(self):
        # db = papis.database.get()
        # bibpath = os.path.join(
            # os.path.dirname(os.path.abspath(__file__)),
            # 'data', 'lib1.bib'
        # )
        # result = self.invoke([
            # 'krishnamurti', '--from-bibtex', bibpath, '-bf', '--all'
        # ])
        # docs = db.query_dict(dict(author='krishnamurti'))
        # self.assertTrue(docs)
        # self.assertTrue(
            # re.match(r' *10.1002/andp.19053221004 *', docs[0]['doi'])
        # )
        # self.assertTrue(
            # re.match(r'.*Krishnamurti.*', docs[0]['author']) is None
        # )
        # self.assertEqual(
            # r' Zur Elektrodynamik bewegter K\"{o}rper ',
            # docs[0]['title']
        # )
