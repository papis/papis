import os
import logging

import whoosh
import whoosh.index
import whoosh.qparser

import papis.config
import papis.document
import papis.database.base
import papis.database.cache

class Database(papis.database.base.Database):

    index = None
    schema = None

    def __init__(self, library=None):
        papis.database.base.Database.__init__(self, library)

    def clear(self):
        whoosh.index.create_in(self.get_index_dir())

    def create_index(self):
        self.logger.debug('Creating index...')
        index_dir = self.get_index_dir()
        if not os.path.exists(index_dir):
            self.logger.debug('Creating dir %s' % index_dir)
            os.makedirs(index_dir)
        whoosh.index.create_in(self.get_index_dir(), self.get_schema())

    def index_exists(self):
        return whoosh.index.exists_in(self.get_index_dir())

    def get_index_dir(self):
        return os.path.join(
            papis.database.cache.get_cache_home(),
            'whoosh',
            papis.database.cache.get_name(self.get_dir())
        )

    def get_index_file(self):
        return os.path.join(
            self.get_index_dir(),
            papis.database.cache.get_name(self.get_dir())
        )

