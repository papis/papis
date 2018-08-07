import papis.database.tests

class Test(papis.database.tests.DatabaseTest):

    @classmethod
    def setUpClass(cls):
        papis.config.set('database-backend', 'papis')
        papis.database.tests.DatabaseTest.setUpClass()

    def test_query(self):
        database = papis.database.get()
        docs = database.query('.')
        self.assertTrue(len(docs) > 0)

