import os
import sys
import papis.config
import papis.database
import unittest
import papis.tests
import tempfile
import papis.database.tests.test_whoosh

class Test(papis.database.tests.test_whoosh.Test):

    @classmethod
    def setUpClass(cls):
        papis.config.set('database-backend', 'papis')
        assert(papis.config.get('database-backend') == 'papis')
        papis.tests.setup_test_library()

        os.environ['XDG_CACHE_HOME'] = tempfile.mkdtemp(prefix='papis-db-test')

        libdir = papis.config.get('dir')
        assert(os.path.exists(libdir))
        assert(papis.config.get_lib() == papis.tests.get_test_lib())

        database = papis.database.get(papis.config.get_lib())
        database.clear()
        database.initialize()
        assert(database is not None)
        assert(database.get_lib() == papis.config.get_lib())
        assert(database.get_dir() == libdir)

    def test_query(self):
        database = papis.database.get()
        docs = database.query('.')
        self.assertTrue(len(docs) > 0)

