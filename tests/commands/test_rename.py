import os

import papis.database
from papis.commands.rename import run

import tests
import tests.cli


class Test(tests.cli.TestWithLibrary):

    def get_docs(self):
        db = papis.database.get()
        return db.get_all_documents()

    def test_simple_update(self) -> None:
        docs = self.get_docs()
        document = docs[0]
        title = document["title"]
        new_name = "Some title with spaces too"
        run(document, new_name)
        docs = papis.database.get().query_dict(dict(title=title))
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].get_main_folder_name(), new_name)
        self.assertTrue(os.path.exists(docs[0].get_main_folder()))
