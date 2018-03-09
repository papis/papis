import os
import papis.bibtex
import json
import yaml
import tempfile
import unittest
import papis.tests
import papis.config
from papis.commands.browse import run

# TODO: Implement meaningful tests
class Test(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        papis.tests.setup_test_library()

    def get_docs(self):
        db = papis.database.get()
        return db.get_all_documents()

    def test_run_function_exists(self):
        self.assertTrue(run is not None)

