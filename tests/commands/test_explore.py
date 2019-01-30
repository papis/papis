import papis.bibtex
import unittest
import tests
import papis.config
from papis.commands.explore import cli
import tempfile
import os
import re


class TestCli(tests.cli.TestCli):

    cli = cli

    def test_main(self):
        self.do_test_cli_function_exists()
        self.do_test_help()

    def test_cmd(self):
        result = self.invoke([
            'cmd', 'ls'
        ])
        self.assertTrue(result.exit_code == 0)

    def test_lib(self):
        result = self.invoke([
            'lib', 'krishnamurti'
        ])
        self.assertTrue(result.exit_code == 0)

    def test_export_bibtex(self):
        path = tempfile.mktemp()
        result = self.invoke([
            'lib', 'krishnamurti', 'export', '--bibtex', path
        ])
        self.assertTrue(result.exit_code == 0)
        self.assertTrue(os.path.exists(path))
        with open(path) as fd:
            bibtex = fd.read()
        expected_bibtex = (
            '@article{1,',
            '  year = {2009},',
            '  title = {Freedom from the known},',
            '  author = {J. Krishnamurti},',
            '}'
        )

        for chunk in expected_bibtex:
            self.assertTrue(chunk in bibtex.split('\n'))

    def test_export_yaml(self):
        path = tempfile.mktemp()
        result = self.invoke([
            'lib', 'krishnamurti', 'export', '--yaml', path
        ])
        self.assertTrue(result.exit_code == 0)
        self.assertTrue(os.path.exists(path))
        with open(path) as fd:
            yaml = fd.read()
        expected_yaml = (
            r'_test_files: 1\n'
            r'author: J. Krishnamurti\n'
            r'files: .*\n'
            r'title: Freedom from the known\n'
            r"year: '2009'\n"
        )

        self.assertTrue(re.match(expected_yaml, yaml))

    def test_citations(self):
        path = tempfile.mktemp()
        result = self.invoke([
            'lib', 'krishnamurti', 'export', '--yaml', path
        ])
        self.assertTrue(result.exit_code == 0)
        self.assertTrue(os.path.exists(path))
        with open(path) as fd:
            yaml = fd.read()
        expected_yaml = (
            r'_test_files: 1\n'
            r'author: J. Krishnamurti\n'
            r'files: .*\n'
            r'title: Freedom from the known\n'
            r"year: '2009'\n"
        )

        self.assertTrue(re.match(expected_yaml, yaml))

    def test_citations_and_json(self):
        path = tempfile.mktemp()
        result = self.invoke([
            'citations', 'krishnamurti', 'export', '--json', path
        ])
        self.assertTrue(result.exit_code == 0)
        with open(path) as fd:
            yaml = fd.read()
        self.assertTrue(yaml == '[]')
