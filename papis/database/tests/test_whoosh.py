import papis.database.tests

class Test(papis.database.tests.DatabaseTest):

    @classmethod
    def setUpClass(cls):
        papis.config.set('database-backend', 'whoosh')
        papis.database.tests.DatabaseTest.setUpClass()

    def test_query(self):
        # The database is existing right now, which means that the
        # test library is in place and therefore we have some documents
        database = papis.database.get()
        docs = database.query('*')
        self.assertTrue(len(docs) > 0)
