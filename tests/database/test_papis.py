import tests.database
import papis.config
import papis.database
import papis.document
import os

class Test(tests.database.DatabaseTest):

    @classmethod
    def setUpClass(cls):
        papis.config.set('database-backend', 'papis')
        tests.database.DatabaseTest.setUpClass()

    def test_backend_name(self):
        self.assertTrue(papis.config.get('database-backend') == 'papis')

    def test_query(self):
        database = papis.database.get()
        docs = database.query('.')
        self.assertTrue(len(docs) > 0)

    def test_sort_string(self):
        database = papis.database.get()
        title_sorted_docs = database.query('.', sort_field='title')

        self.assertEqual(papis.document.to_dict(title_sorted_docs[0])['title'],
                         'Test Document 1')

    def test_sort_int(self):
        database = papis.database.get()
        year_sorted_docs = database.query('.', sort_field='year')
        self.assertEqual(papis.document.to_dict(year_sorted_docs[0])['year'],
                         '1093')

    def test_cache_path(self):
        database = papis.database.get()
        assert(os.path.exists(database._get_cache_file_path()))

    def test_load_again(self):
        db = papis.database.get()
        Ni = len(db.get_documents())
        db.save()
        db.documents = None
        # Now the pickled path exists but no documents
        Nf = len(db.get_documents())
        self.assertEqual(Ni, Nf)

    def test_failed_location_in_cache(self):
        db = papis.database.get()
        doc = db.get_documents()[0]
        db.delete(doc)
        try:
            db._locate_document(doc)
        except Exception as e:
            self.assertTrue(True)
        else:
            self.assertTrue(False)
