import tests.database
import papis.config
import papis.database

class Test(tests.database.DatabaseTest):

    @classmethod
    def setUpClass(cls):
        papis.config.set('database-backend', 'whoosh')
        tests.database.DatabaseTest.setUpClass()

    def test_backend_name(self):
        self.assertTrue(papis.config.get('database-backend') == 'whoosh')

    def test_query(self):
        # The database is existing right now, which means that the
        # test library is in place and therefore we have some documents
        database = papis.database.get()
        docs = database.query('*')
        self.assertTrue(len(docs) > 0)
