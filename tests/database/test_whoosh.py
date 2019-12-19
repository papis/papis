import tests.database
import papis.config
import papis.database
import papis.document

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

    def test_sort(self):
        database = papis.database.get()
        docs = database.query('*', sort_field='title')
        print([papis.document.to_dict(doc)['title'] for doc in docs])
        self.assertEqual(papis.document.to_dict(docs[0])['title'], 'Freedom from the known')

    def test_python_sort(self):
        database = papis.database.get()
        docs = database.query('*', sort_field='doi')
        self.assertEqual(papis.document.to_dict(docs[0])['doi'], '10.1021/ct5004252')
