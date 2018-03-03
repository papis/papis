import os
import sys
import papis.config
import papis.document
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

    def test_update(self):
        database = papis.database.get()
        doc = database.get_all_documents()[0]
        self.assertTrue(doc is not None)
        doc['title'] = 'test_update test'
        doc.save()
        database.update(doc)
        docs = database.query_dict({'title': 'test_update test'})
        self.assertTrue(len(docs) == 1)
        doc = docs[0]
        self.assertTrue(doc is not None)
        self.assertTrue(doc['title'] == 'test_update test')

    def test_delete(self):
        database = papis.database.get()
        docs = database.get_all_documents()
        Ni = len(docs)
        self.assertTrue(Ni > 1)
        database.delete( docs[0] )
        papis.document.delete( docs[0] )
        docs = database.get_all_documents()
        Nf = len(docs)
        self.assertTrue(Ni - Nf > 0)

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
        docs = database.get_all_documents()
        N = len(docs)
        newdocs = [
            papis.document.from_data(data)
            for data in papis.tests.test_data
        ]
        for j,doc in enumerate(newdocs):
            doc.set_folder(tempfile.mkdtemp())
            doc['tempfile'] = doc.get_main_folder()
            doc.save()
            folder = os.path.join(
                database.get_dir(),
                'new',
                str(j+N)
            )
            papis.document.move(doc, folder)
            print(doc)
            print(doc.get_main_folder())
            database.add(doc)
        docs = database.get_all_documents()
        self.assertEqual(len(docs), N+2)

    def test_clear(self):
        database = papis.database.get()
        database.clear()
        database.initialize()
        self.test_get_all_documents()

    def test_backend_name(self):
        self.assertTrue(papis.database.get().get_backend_name() is not None)
