import tests.database
import papis.config
import papis.database
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

    def test_cache_path(self):
        database = papis.database.get()
        assert(os.path.exists(database._get_cache_file_path()))
