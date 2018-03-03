import os
import sys
import papis.config
import papis.database.whoosh
import papis.database
import unittest
import papis.tests
import tempfile

class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        papis.config.set('database-backend', 'whoosh')
        assert(papis.config.get('database-backend') == 'whoosh')
        papis.tests.setup_test_library()

        os.environ['XDG_CACHE_HOME'] = tempfile.mkdtemp(prefix='whoosh-test')

        libdir = papis.config.get('dir')
        assert(os.path.exists(libdir))
        assert(papis.config.get_lib() == papis.tests.get_test_lib())

        database = papis.database.get(papis.config.get_lib())
        database.clear()
        database.initialize()
        assert(database is not None)
        assert(database.get_lib() == papis.config.get_lib())
        assert(database.get_dir() == libdir)

    def test_check_database(self):
        database = papis.database.get()
        self.assertTrue(database is not None)
        self.assertTrue(database.get_lib() == papis.tests.get_test_lib())

    def test_get_all_documents(self):
        database = papis.database.get()
        docs = database.get_all_documents()
        self.assertTrue(len(docs) > 0)

    def test_query(self):
        # The database is existing right now, which means that the
        # test library is in place and therefore we have some documents
        database = papis.database.get()
        docs = database.query('*')
        self.assertTrue(len(docs) > 0)

    def test_add(self):
        database = papis.database.get()
        docs = database.query('*')
        N = len(docs)
        docs = [
            papis.document.from_data(data)
            for data in papis.tests.test_data
        ]
        self.assertTrue(N > 0)
        for doc in docs:
            database.add(doc)
        docs = database.query('*')
        self.assertEqual(len(docs), N+2)
