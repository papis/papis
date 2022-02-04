import papis.bibtex
import json
import yaml
import tempfile
import unittest
import tests
import tests.cli
import papis.config
import papis.document
from papis.commands.export import run, cli
import re
import os
import glob

# NOTE: try to use the CLoader when possible, as it's a lot faster than the
# python version, at least at the time of writing
try:
    from yaml import CSafeLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader  # type: ignore[misc]


class TestRun(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        tests.setup_test_library()

    def get_docs(self):
        db = papis.database.get()
        return db.get_all_documents()

    def test_bibtex(self):
        docs = self.get_docs()
        string = run(docs, to_format='bibtex')
        self.assertTrue(len(string) > 0)
        data = papis.bibtex.bibtex_to_dict(string)
        self.assertTrue(len(data) > 0)

    def test_json(self):
        docs = self.get_docs()
        string = run(docs, to_format='json')
        self.assertTrue(len(string) > 0)
        data = json.loads(string)
        self.assertTrue(len(data) > 0)

    def test_yaml(self):
        docs = self.get_docs()
        string = run(docs, to_format='yaml')
        self.assertTrue(len(string) > 0)
        yamlfile = tempfile.mktemp()
        with open(yamlfile, 'w+') as fd:
            fd.write(string)
        with open(yamlfile) as fd:
            data = list(yaml.load_all(fd, Loader=Loader))
        self.assertTrue(data is not None)
        self.assertTrue(len(list(data)) > 0)


class TestCli(tests.cli.TestCli):

    cli = cli

    def test_main(self):
        self.do_test_cli_function_exists()
        self.do_test_help()

    def test_json(self):

        # output stdout
        result = self.invoke([
            'krishnamurti', '--format', 'json'
        ])
        self.assertTrue(result.exit_code == 0)
        data = json.loads(result.stdout_bytes.decode())
        assert(isinstance(data, list))
        assert(len(data) == 1)
        assert(re.match(r'.*Krishnamurti.*', data[0]['author']) is not None)

        # output stdout
        outfile = tempfile.mktemp()
        self.assertTrue(not os.path.exists(outfile))
        result = self.invoke([
            'Krishnamurti', '--format', 'json', '--out', outfile
        ])
        self.assertTrue(result.exit_code == 0)
        self.assertTrue(os.path.exists(outfile))

        with open(outfile) as fd:
            data = json.load(fd)
            assert(isinstance(data, list))
            assert(len(data) == 1)
            assert(re.match(r'.*Krishnamurti.*', data[0]['author']) is not None)

    def test_yaml(self):

        # output stdout
        result = self.invoke([
            'krishnamurti', '--format', 'yaml'
        ])
        self.assertTrue(result.exit_code == 0)
        data = yaml.safe_load(result.stdout_bytes)
        assert(re.match(r'.*Krishnamurti.*', data['author']) is not None)

        # output stdout
        outfile = tempfile.mktemp()
        self.assertTrue(not os.path.exists(outfile))
        result = self.invoke([
            'Krishnamurti', '--format', 'yaml', '--out', outfile
        ])
        self.assertTrue(result.exit_code == 0)
        self.assertTrue(os.path.exists(outfile))

        with open(outfile) as fd:
            data = yaml.safe_load(fd.read())
            assert(data is not None)
            assert(re.match(r'.*Krishnamurti.*', data['author']) is not None)

    def test_folder(self):
        outdir = tempfile.mktemp()
        self.assertTrue(not os.path.exists(outdir))
        # output stdout
        result = self.invoke(['krishnamurti', '--folder', '--out', outdir])
        self.assertTrue(os.path.exists(outdir))
        self.assertTrue(os.path.isdir(outdir))
        self.assertTrue(result.exit_code == 0)
        self.assertTrue(result.stdout_bytes == b'')
        doc = papis.document.from_folder(outdir)
        self.assertTrue(doc is not None)
        assert(re.match(r'.*Krishnamurti.*', doc['author']) is not None)

    def test_folder_all(self):
        outdir = tempfile.mktemp()
        self.assertTrue(not os.path.exists(outdir))
        # output stdout
        result = self.invoke(['--all', '--folder', '--out', outdir])
        self.assertTrue(os.path.exists(outdir))
        self.assertTrue(os.path.isdir(outdir))
        self.assertTrue(result.exit_code == 0)
        self.assertTrue(result.stdout_bytes == b'')
        dirs = glob.glob(os.path.join(outdir, '*'))
        self.assertTrue(len(dirs) > 1)
        for l in dirs:
            self.assertTrue(os.path.exists(l))
            self.assertTrue(os.path.isdir(l))

    def test_no_documents(self):
        result = self.invoke(['-f', 'bibtex', '__no_document__'])
        self.assertTrue(result.exit_code == 0)
