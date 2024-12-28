"""This is the Whoosh interface to Papis.

For future Papis developers here are some considerations.

Whoosh works with 3 main objects, the ``Index``, the ``Writer`` and the ``Schema``.
The indices are stored in a subfolder of :func:`~papis.utils.get_cache_home`.
The name of the indices folders is similar to the cache files of the ``papis``
cache database.

Once the Index is created in the mentioned folder, a Schema is initialized,
which is a declaration of the data prototype of the database, or the
definition of the table in SQL parlance. This is controlled by the
Papis configuration through the :confval:`whoosh-schema-prototype`. For instance
if the database is supposed to only contain the key fields
``[author, title, year, tags]``, then the :confval:`whoosh-schema-prototype`
string should look like the following:

.. code:: python

    {
        "author": TEXT(stored=True),
        "title": TEXT(stored=True),
        "year": TEXT(stored=True),
        "tags": TEXT(stored=True),
    }

where all the fields are explained in the Whoosh
`documentation <https://whoosh.readthedocs.io/en/latest/schema.html>`__.

After this Schema is created, the folders of the library are traversed
and the documents are added to the database. When adding documents, only the
keys in the schema are stored. This means that, e.g., if ``publisher`` is not in
the schema you will not be able to search for the publisher through a query.
"""

import os
from typing import List, Dict, Optional, KeysView, TYPE_CHECKING

import papis.config
import papis.logging
from papis.database.base import Database as DatabaseBase, get_cache_file_name
from papis.document import Document, describe, from_folder
from papis.exceptions import DocumentFolderNotFound
from papis.id import ID_KEY_NAME
from papis.library import Library

if TYPE_CHECKING:
    from whoosh.index import Index
    from whoosh.fields import Schema, FieldType
    from whoosh.writing import IndexWriter

logger = papis.logging.get_logger(__name__)

#: Field name used to store the document main folder the the Whoosh database.
WHOOSH_FOLDER_FIELD = "papis-folder"


class Database(DatabaseBase):
    def __init__(self, library: Optional[Library] = None) -> None:
        super().__init__(library)

        from papis.utils import get_cache_home

        self.cache_dir = os.path.join(get_cache_home(), "database", "whoosh")
        self.index_dir = os.path.expanduser(
            os.path.join(self.cache_dir, get_cache_file_name(self.lib.path_format()))
            )

        self.initialize()

    def get_backend_name(self) -> str:
        return "whoosh"

    def get_cache_path(self) -> str:
        return self.index_dir

    def get_all_query_string(self) -> str:
        return "*"

    def initialize(self) -> None:
        if self._index_exists():
            index = self._get_index()

            user_fields = self._get_schema_init_fields()
            db_fields = index.schema

            # NOTE: the database should be rebuilt if new fields have been added
            # or if the field types have been changed in any way by the user
            rebuild_db = (
                set(user_fields) != set(db_fields.names())
                or any(user_fields[name] != db_fields[name] for name in user_fields)
            )
            if not rebuild_db:
                logger.debug("Initialized index found for library.")
                return

            logger.debug("Rebuilding database because fields do not match.")
            self.clear()
        else:
            logger.info("Indexing library. This might take a while...")

        self._create_index()
        self._index_documents()

    def clear(self) -> None:
        import shutil
        if self._index_exists():
            logger.warning("Clearing the database at '%s'...", self.get_cache_path())
            shutil.rmtree(self.index_dir)

    def add(self, document: Document) -> None:
        logger.debug("Adding document: '%s'.", describe(document))
        schema_keys = self._get_schema_init_fields().keys()
        index = self._get_index()
        writer = index.writer()

        self._add_document_with_writer(document, writer, schema_keys)
        writer.commit()

    def update(self, document: Document) -> None:
        self.delete(document)
        self.add(document)

    def delete(self, document: Document) -> None:
        logger.debug("Deleting document: '%s'.", describe(document))
        index = self._get_index()
        writer = index.writer()

        writer.delete_by_term(ID_KEY_NAME, document[ID_KEY_NAME])
        writer.commit()

    def query(self, query_string: str) -> List[Document]:
        logger.debug("Querying database for '%s'.", query_string)

        import time
        from whoosh.qparser import MultifieldParser, FuzzyTermPlugin

        index = self._get_index()
        qp = MultifieldParser(["title", "author", "tags"], schema=index.schema)
        qp.add_plugin(FuzzyTermPlugin())

        t_start = time.time()
        query = qp.parse(query_string)
        with index.searcher() as searcher:
            results = searcher.search(query, limit=None)
            documents = [from_folder(r.get(WHOOSH_FOLDER_FIELD)) for r in results]

        t_delta = 1000 * (time.time() - t_start)
        logger.debug("Finished querying in %.2fms (%d docs).", t_delta, len(documents))

        return documents

    def query_dict(self, query: Dict[str, str]) -> List[Document]:
        query_string = " AND ".join(f'{key}:"{val}" ' for key, val in query.items())
        return self.query(query_string)

    def get_all_documents(self) -> List[Document]:
        return self.query(self.get_all_query_string())

    def _create_index(self) -> None:
        """Create a new index.

        If an index already exists, this will delete it and create a new one.
        """
        logger.debug("Creating index.")
        if not os.path.exists(self.index_dir):
            logger.debug("Creating index directory '%s'.", self.index_dir)
            os.makedirs(self.index_dir)

        from whoosh.index import create_in
        create_in(self.index_dir, self._create_schema())

    def _index_exists(self) -> bool:
        """Check if index already exists in :attr:`index_dir`."""
        from whoosh.index import exists_in
        return bool(exists_in(self.index_dir))

    def _add_document_with_writer(self,
                                  document: Document,
                                  writer: "IndexWriter",
                                  schema_keys: KeysView[str]) -> None:
        """Helper function that adds a document document (without committing).

        This function does only two things: creates a suitable dictionary to be
        added to the database and adds it to the writer. It does not commit the
        change to the writer, so that has to be done separately.
        """
        # NOTE: `maybe_compute_id` overwrites the info file, so put it before
        # anything else, otherwise get `WHOOSH_FOLDER_FIELD` in your info.yaml
        self.maybe_compute_id(document)

        folder = document.get_main_folder()
        if not folder:
            raise DocumentFolderNotFound(describe(document))

        doc_schema = {
            k: (folder if k == WHOOSH_FOLDER_FIELD else str(document[k]))
            for k in schema_keys
        }
        writer.add_document(**doc_schema)

    def _index_documents(self) -> None:
        """Initializes the database with an index of all the documents.

        This function basically it goes through all folders from the library
        (that contain an `info.yaml` file) and adds the documents to the database
        index. It is quite expensive and will only be called if no index is present
        or a rebuild is necessary.
        """
        from papis.utils import get_folders, folders_to_documents

        logger.debug("Indexing the library, this might take a while...")
        folders = [f for path in self.lib.paths for f in get_folders(path)]
        documents = folders_to_documents(folders)

        schema_keys = self._get_schema_init_fields().keys()
        index = self._get_index()
        writer = index.writer()

        for doc in documents:
            self._add_document_with_writer(doc, writer, schema_keys)
        writer.commit()

    def _get_index(self) -> "Index":
        """Gets the index for the current library
        """
        from whoosh.index import open_dir
        return open_dir(self.index_dir)

    def _create_schema(self) -> "Schema":
        """Creates and returns Whoosh schema to be applied to the library"""
        from whoosh.fields import Schema
        logger.debug("Creating schema.")

        fields = self._get_schema_init_fields()
        return Schema(**fields)

    def _get_schema_init_fields(self) -> Dict[str, "FieldType"]:
        """
        :returns: the keyword arguments to be passed to the Whoosh schema object
            (see :meth:`_create_schema`).
        """
        # NOTE: these are imported here so that `eval` sees them
        from whoosh.fields import TEXT, ID, KEYWORD, STORED  # noqa: F401

        # TODO: this is a security risk, find a way to fix it
        user_prototype = eval(papis.config.getstring("whoosh-schema-prototype"))

        # add default fields that should always be in the database
        fields = {
            ID_KEY_NAME: ID(stored=True, unique=True),
            WHOOSH_FOLDER_FIELD: TEXT(stored=True)
        }
        # add user provided fields
        fields.update(user_prototype)

        # add simpler text fields
        fields_list = papis.config.getlist("whoosh-schema-fields")
        for field in fields_list:
            fields.update({field: TEXT(stored=True)})

        return fields
