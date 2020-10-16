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
            'lib', 'krishnamurti', 'export', '--format', 'bibtex', '-o', path
        ])
        self.assertTrue(result.exit_code == 0)
        self.assertTrue(os.path.exists(path))
        with open(path) as fd:
            bibtex = fd.read()
        expected_bibtex = (
            '@article{FreedomFromThJKri2009,',
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
            'lib', 'krishnamurti', 'export', '--format', 'yaml', '-o', path
        ])
        self.assertTrue(result.exit_code == 0)
        self.assertTrue(os.path.exists(path))
        with open(path) as fd:
            yaml = fd.read()
        expected_yaml = (
            r'author: J. Krishnamurti',
            r'title: Freedom from the known',
            r"year: '2009'"
        )

        for ey in expected_yaml:
            self.assertTrue(re.findall(ey, yaml))

    def test_citations_and_json(self):
        path = tempfile.mktemp()
        result = self.invoke([
            'citations', 'krishnamurti', 'export', '--format', 'json', '--out',
            path
        ])
        self.assertTrue(result.exit_code == 0)
        with open(path) as fd:
            yaml = fd.read()
        self.assertTrue(yaml == '[]')
