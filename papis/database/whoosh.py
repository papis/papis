"""This is the whoosh interface to papis. For future papis developers
here are some considerations.

Whoosh works with 3 main objects, the Index, the Writer and the Schema.
The indices are stored in a folder which by default is in
``$XDG_CACHE_HOME/papis/whoosh``. The name of the indices
folders is similar to the cache files of the papis cache database.

Once the index is created in the mentioned folder, a Schema is initialized,
which is a declaration of the data prototype of the database, or the
definition of the table in sql parlance. This is controlled by the
papis configuration through the `whoosh-schema-prototype`. For instance
if the database is supposed to only contain the key fields
``author``, ``title``, ``year`` and ``tags``, then the
``whoosh-schema-prototype`` STRING should look like the following:

::

        {
            "author": TEXT(stored=True),
            "title": TEXT(stored=True),
            "year": TEXT(stored=True),
            "tags": TEXT(stored=True),
        }

where all the fields are explained in the whoosh
`documentation <https://whoosh.readthedocs.io/en/latest/schema.html/>`_.

After this Schema is created, the folders of the library are recursed over
and the documents are added to the database where only these
properties are stored. This means, if ``publisher`` is not in the above list,
you will not be able to parse the publisher through a search.

.. note::

    This is a point where maybe a great deal of discussion and optimization
    should be made.



"""
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

    def __init__(self, library=None):
        papis.database.base.Database.__init__(self, library)
        self.logger = logging.getLogger('db:whoosh')
        self.initialize()

    def get_backend_name(self):
        return 'whoosh'

    def clear(self):
        import shutil
        if self.index_exists():
            self.logger.warning('Clearing the database')
            shutil.rmtree(self.get_index_dir())
        else:
            self.logger.warning(
                'Trying to clear database, but no database found'
            )

#   TODO
    def match(self, document, query_string):
        pass

    def add(self, document):
        schema_keys = self.get_schema_init_fields().keys()
        self.logger.debug("adding document")
        writer = self.get_writer()
        self.add_document_with_writer(document, writer, schema_keys)
        self.logger.debug("commiting document..")
        writer.commit()

    def update(self, document):
        """As it says in the docs, just delete the document and add it again
        """
        self.delete(document)
        self.add(document)

    def delete(self, document):
        writer = self.get_writer()
        self.logger.debug("deleting document..")
        writer.delete_by_term(
            self.get_id_key(),
            self.get_id_value(document)
        )
        self.logger.debug("commiting deletion..")
        writer.commit()

    def query_dict(self, dictionary):
        query_string = " AND ".join(
            ["{}:\"{}\" ".format(key, val) for key, val in dictionary.items()]
        )
        return self.query(query_string)

    def query(self, query_string):
        self.logger.debug('Query string %s' % query_string)
        index = self.get_index()
        qp = whoosh.qparser.MultifieldParser(
            ['title', 'author', 'tags'],
            schema=self.get_schema()
        )
        qp.add_plugin(whoosh.qparser.FuzzyTermPlugin())
        query = qp.parse(query_string)
        with index.searcher() as searcher:
            results = searcher.search(query, limit=None)
            self.logger.debug(results)
            documents = [
                papis.document.from_folder(r.get(self.get_id_key()))
                for r in results
            ]
        return documents

    def get_all_query_string(self):
        return '*'

    def get_all_documents(self):
        return self.query(self.get_all_query_string())

    def get_id_key(self):
        """Get the unique key identifier name of the documents in the database

        :returns: key identifier
        :rtype:  str
        """
        return 'whoosh_id_'

    def get_id_value(self, document):
        """Get the value that is stored in the unique key identifier
        of the documents in the database. In the case of papis this is
        just the path of the documents.

        :param document: Papis document
        :type  document: papis.document.Document
        :returns: Path for the document
        :rtype:  str
        """
        return document.get_main_folder()

    def create_index(self):
        """Create a brand new index, notice that if an index already
        exists it will delete it and create a new one.
        """
        self.logger.debug('Creating index...')
        index_dir = self.get_index_dir()
        if not os.path.exists(index_dir):
            self.logger.debug('Creating dir %s' % index_dir)
            os.makedirs(index_dir)
        whoosh.index.create_in(self.get_index_dir(), self.create_schema())

    def index_exists(self):
        """Check if index already exists in get_index_dir()
        """
        return whoosh.index.exists_in(self.get_index_dir())

    def add_document_with_writer(self, document, writer, schema_keys):
        """Helper function that takes a writer and a dictionary
        containing the keys of the schema and adds the document to the writer.
        Notice that this function does only two things, creating a suitable
        dictionary to be added to the database and adding it to the writer.
        It DOES NOT commit the change to the writer, this has to be done
        separately.

        :param document: Papis document
        :type  document: papis.document.Document
        :param writer: Whoosh writer
        :type  writer: whoosh.writer
        :param schema_keys: Dictionary containing the defining keys of the
            database Schema
        :type  schema_keys: dict
        """
        doc_d = dict()
        doc_d.update(
            {
                k: str(document[k]) or ''
                for k in schema_keys
            }
        )
        doc_d[self.get_id_key()] = self.get_id_value(document)
        writer.add_document(**doc_d)

    def do_indexing(self):
        """This function initializes the database. Basically it goes through
        all folders from the library (that contain an `info.yaml` file)
        and adds the documents to the database index. This function is
        expensive and will be called only if no index is present, so
        at the time of building a brand new index.
        """
        self.logger.debug('Indexing the library, this might take a while...')
        folders = papis.utils.get_folders(self.get_dir())
        documents = papis.database.cache.folders_to_documents(folders)
        schema_keys = self.get_schema_init_fields().keys()
        writer = self.get_writer()
        for doc in documents:
            self.add_document_with_writer(doc, writer, schema_keys)
        writer.commit()

    def initialize(self):
        """Function to be called everytime a database object is created.
        It checks if an index exists, if not, it creates one and
        indexes the library.
        """
        if self.index_exists():
            self.logger.debug('Initialized index found for library')
            return True
        self.create_index()
        self.do_indexing()

    def get_index(self):
        """Gets the index for the current library

        :returns: Index
        :rtype:  whoosh.index
        """
        return whoosh.index.open_dir(self.get_index_dir())

    def get_writer(self):
        """Gets the writer for the current library

        :returns: Writer
        :rtype:  whoosh.writer
        """
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
        from whoosh.fields import TEXT, ID, KEYWORD, STORED
        # This part is non-negotiable
        fields = {self.get_id_key(): ID(stored=True, unique=True)}
        user_prototype = eval(
            papis.config.get('whoosh-schema-prototype')
        )
        fields.update(user_prototype)
        fields_list = eval(papis.config.get('whoosh-schema-fields'))
        if not isinstance(fields_list, list):
            raise Exception('whoosh-schema-fields should be a python list')
        for field in fields_list:
            fields.update({field: TEXT(stored=True)})
        # self.logger.debug('Schema prototype: {}'.format(fields))
        return fields

    def get_cache_dir(self):
        """Get general directory to store whoosh indexes.

        :returns: Full path to whoosh cache home directory
        :rtype:  str
        """
        path = os.path.join(
            papis.database.cache.get_cache_home(),
            'whoosh'
        )
        # self.logger.debug('Cache dir %s' % path)
        return path

    def get_index_dir(self):
        """Get the directory inside `get_cache_dir` to store the index.
        :returns: Full path to index dir
        :rtype:  str
        """
        path = os.path.expanduser(
            os.path.join(
                self.get_cache_dir(),
                papis.database.cache.get_name(self.get_dir())
            )
        )
        # self.logger.debug('Index dir %s' % path)
        return path
