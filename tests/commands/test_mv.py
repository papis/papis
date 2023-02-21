import os
import tempfile

import papis.database
import papis.commands.mv

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
        new_dir = tempfile.mkdtemp()
        self.assertTrue(os.path.exists(new_dir))
        papis.commands.mv.run(document, new_dir)
        docs = papis.database.get().query_dict(dict(title=title))
        self.assertEqual(len(docs), 1)
        self.assertEqual(os.path.dirname(docs[0].get_main_folder()), new_dir)
        self.assertEqual(
            docs[0].get_main_folder(),
            os.path.join(new_dir, os.path.basename(docs[0].get_main_folder()))
        )
