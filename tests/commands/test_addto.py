import unittest

import papis.config
from papis.commands.addto import run

import tests
import tests.cli


class Test(tests.cli.TestWithLibrary):

    def test_simple_add(self) -> None:
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
