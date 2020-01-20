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
from whoosh.fields import Schema, FieldType
from whoosh.writing import IndexWriter

import papis.config
import papis.strings
import papis.document
import papis.database.base
import papis.database.cache
from papis.utils import get_cache_home, get_folders, folders_to_documents

from typing import List, Dict, Optional, Any, KeysView


class Database(papis.database.base.Database):

    def __init__(self, library: Optional[papis.library.Library] = None):
        papis.database.base.Database.__init__(self, library)
        self.logger = logging.getLogger('db:whoosh')
        self.cache_dir = os.path.join(get_cache_home(), 'database', 'whoosh')
        self.index_dir = os.path.expanduser(
            os.path.join(
                self.cache_dir,
                papis.database.cache.get_cache_file_name(
                    self.lib.path_format()
                )))  # type: str

        self.initialize()

    def get_backend_name(self) -> str:
        return 'whoosh'

    def clear(self) -> None:
        import shutil
        if self.index_exists():
            self.logger.warning('Clearing the database')
            shutil.rmtree(self.index_dir)

    def add(self, document: papis.document.Document) -> None:
        schema_keys = self.get_schema_init_fields().keys()
        self.logger.debug("adding document")
        writer = self.get_writer()
        self.add_document_with_writer(document, writer, schema_keys)
        self.logger.debug("commiting document..")
        writer.commit()

    def update(self, document: papis.document.Document) -> None:
        """As it says in the docs, just delete the document and add it again
        """
        self.delete(document)
        self.add(document)

    def delete(self, document: papis.document.Document) -> None:
        writer = self.get_writer()
        self.logger.debug("deleting document..")
        writer.delete_by_term(
            self.get_id_key(),
            self.get_id_value(document))
        self.logger.debug("commiting deletion..")
        writer.commit()

    def query_dict(
            self, dictionary: Dict[str, str]) -> List[papis.document.Document]:
        query_string = " AND ".join(
            ["{}:\"{}\" ".format(key, val)
                for key, val in dictionary.items()])
        return self.query(query_string)

    def query(self, query_string: str) -> List[papis.document.Document]:
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
                for r in results]
        return documents

    def get_all_query_string(self) -> str:
        return '*'

    def get_all_documents(self) -> List[papis.document.Document]:
        return self.query(self.get_all_query_string())

    def get_id_key(self) -> str:
        """Get the unique key identifier name of the documents in the database

        :returns: key identifier
        :rtype:  str
        """
        return 'whoosh_id_'

    def get_id_value(self, document: papis.document.Document) -> str:
        """Get the value that is stored in the unique key identifier
        of the documents in the database. In the case of papis this is
        just the path of the documents.

        :param document: Papis document
        :type  document: papis.document.Document
        :returns: Path for the document
        :rtype:  str
        """
        _folder = document.get_main_folder()
        if _folder is None:
            raise Exception(papis.strings.no_folder_attached_to_document)
        else:
            return _folder

    def create_index(self) -> None:
        """Create a brand new index, notice that if an index already
        exists it will delete it and create a new one.
        """
        self.logger.debug('Creating index...')
        if not os.path.exists(self.index_dir):
            self.logger.debug('Creating dir %s' % self.index_dir)
            os.makedirs(self.index_dir)
        whoosh.index.create_in(self.index_dir, self.create_schema())

    def index_exists(self) -> Any:
        """Check if index already exists in index_dir()
        """
        return whoosh.index.exists_in(self.index_dir)

    def add_document_with_writer(
            self,
            document: papis.document.Document,
            writer: IndexWriter,
            schema_keys: KeysView[str]) -> None:
        """Helper function that takes a writer and a dictionary
        containing the keys of the schema and adds the document to the writer.
        Notice that this function does only two things, creating a suitable
        dictionary to be added to the database and adding it to the writer.
        It DOES NOT commit the change to the writer, this has to be done
        separately.

        :param document: Papis document
        :type  document: papis.document.Document
        :param writer: Whoosh writer
        :type  writer: whoosh.writing.IndexWriter
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

    def do_indexing(self) -> None:
        """This function initializes the database. Basically it goes through
        all folders from the library (that contain an `info.yaml` file)
        and adds the documents to the database index. This function is
        expensive and will be called only if no index is present, so
        at the time of building a brand new index.
        """
        self.logger.debug('Indexing the library, this might take a while...')
        folders = sum(
                [get_folders(d)
                    for d in self.get_dirs()], [])  # type: List[str]
        documents = folders_to_documents(folders)
        schema_keys = self.get_schema_init_fields().keys()
        writer = self.get_writer()
        for doc in documents:
            self.add_document_with_writer(doc, writer, schema_keys)
        writer.commit()

    def initialize(self) -> None:
        """Function to be called everytime a database object is created.
        It checks if an index exists, if not, it creates one and
        indexes the library.

        If the schema fields have been changed, it updates the database.
        """
        if self.index_exists():
            user_fields = self.get_schema_init_fields()
            db_fields = self.get_schema()

            user_field_names = sorted(list(user_fields))
            db_field_names = sorted(db_fields.names())

            # If the user fields and the fields in the DB
            # aren't the same, then we have to rebuild the
            # database.
            if user_field_names != db_field_names:
                self.rebuild()
                self.logger.debug("Rebuilt database because field names"
                                  "don't match")
            else:
                # Otherwise, verify that the fields are
                # all the same and rebuild if any have
                # changed at all.
                rebuilt_db = False
                for field in user_field_names:
                    if user_fields[field] != db_fields[field]:
                        self.rebuild()
                        self.logger.debug("Rebuilt DB because field types"
                                          " don't match")
                        rebuilt_db = True
                        break

                if not rebuilt_db:
                    self.logger.debug('Initialized index found for library')
                    return
        self.create_index()
        self.do_indexing()

    def rebuild(self) -> None:
        self.clear()
        self.create_index()
        self.do_indexing()

    def get_index(self) -> whoosh.index.Index:
        """Gets the index for the current library

        :returns: Index
        :rtype:  whoosh.index
        """
        return whoosh.index.open_dir(self.index_dir)

    def get_writer(self) -> IndexWriter:
        """Gets the writer for the current library

        :returns: Writer
        :rtype:  whoosh.writer
        """
        return self.get_index().writer()

    def get_schema(self) -> Schema:
        """Gets current schema

        :returns: Whoosch Schema
        :rtype:  whoosh.fields.Schema
        """
        return self.get_index().schema

    def create_schema(self) -> Schema:
        """Creates and returns whoosh schema to be applied to the library

        :returns: Whoosch Schema
        :rtype:  whoosh.fields.Schema
        """
        from whoosh.fields import Schema
        self.logger.debug('Creating schema')
        fields = self.get_schema_init_fields()
        schema = Schema(**fields)
        return schema

    def get_schema_init_fields(self) -> Dict[str, FieldType]:
        """Returns the arguments to be passed to the whoosh schema
        object instantiation found in the method `get_schema`.
        """
        # This we need for the eval code beneath
        from whoosh.fields import TEXT, ID, KEYWORD, STORED  # noqa: F401
        # This part is non-negotiable
        fields = {self.get_id_key(): ID(stored=True, unique=True)}
        # TODO: this is a security risk, find a way to fix it
        user_prototype = eval(
            papis.config.getstring('whoosh-schema-prototype'))  # KeysView[str]
        fields.update(user_prototype)
        fields_list = papis.config.getlist('whoosh-schema-fields')
        for field in fields_list:
            fields.update({field: TEXT(stored=True)})
        # self.logger.debug('Schema prototype: {}'.format(fields))
        return fields
