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
        self.logger = logging.getLogger('db:whoosh')
        self.initialize()

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

    def do_indexing(self):
        self.logger.debug('Indexing the library, this might take a while...')
        folders = papis.utils.get_folders(self.get_dir())
        documents = papis.database.cache.folders_to_documents(folders)
        schema_keys = self.get_schema_init_fields().keys()
        writer = self.get_writer()
        for doc in documents:
            doc_d = dict()
            doc_d.update(
                {
                    k: str(doc[k]) or ''
                    for k in schema_keys
                }
            )
            doc_d['whoosh_id_'] = doc.get_main_folder()
            writer.add_document(**doc_d)
        writer.commit()

    def initialize(self):
        if self.index_exists():
            self.logger.debug('Initialized index found for library')
            return True
        self.create_index()
        self.do_indexing()

    def get_index(self):
        return whoosh.index.open_dir(self.get_index_dir())

    def get_writer(self):
        return self.get_index().writer()

    def get_schema(self):
        """Gets current schema

        :returns: Whoosch Schema
        :rtype:  whoosh.fields.Schema
        """
        return self.get_index().schema

    def create_schema(self):
        """Creates and returns whoosh schema to be applied to the library

        :returns: Whoosch Schema
        :rtype:  whoosh.fields.Schema
        """
        from whoosh.fields import Schema
        self.logger.debug('Creating schema')
        fields = self.get_schema_init_fields()
        schema = Schema(**fields)
        return schema

    def get_schema_init_fields(self):
        """Returns the arguments to be passed to the whoosh schema
        object instantiation found in the method `get_schema`.
        """
        from whoosh.fields import TEXT, KEYWORD, ID, STORED
        import json
        # This part is non-negotiable
        fields = { self.get_id_key(): ID(stored=True, unique=True) }
        user_prototype = eval(
            papis.config.get('whoosh-schema-prototype')
        )
        query = qp.parse(query_string)
        with index.searcher() as searcher:
            results = searcher.search(query, limit=None)
            self.logger.debug(results)
            documents = [
                papis.document.from_folder(r.get('whoosh_id_'))
                for r in results
            ]
        return documents


    def clear(self):
        import shutil
        self.logger.warning('Clearing the database')
        if self.index_exists():
            shutil.rmtree(self.get_index_dir())

    def get_cache_dir(self):
        path = os.path.join(
            papis.database.cache.get_cache_home(),
            'whoosh'
        )
        #self.logger.debug('Cache dir %s' % path)
        return path

    def get_index_dir(self):
        path = os.path.expanduser(
            os.path.join(
                self.get_cache_dir(),
                papis.database.cache.get_name(self.get_dir())
            )
        )
        #self.logger.debug('Index dir %s' % path)
        return path

