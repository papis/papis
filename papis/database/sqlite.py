from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from functools import cached_property
from typing import TYPE_CHECKING

import papis.config
import papis.logging
from papis.database.base import Database

if TYPE_CHECKING:
    from collections.abc import Iterator

    from papis.document import Document
    from papis.library import Library

logger = papis.logging.get_logger(__name__)

#: The name of the table used in the SQLite database.
SQLITE_TABLE_NAME = "documents"

#: A set of known types supported by :mod:`sqlite3`.
SQLITE_ALLOWED_TYPES = {"INTEGER", "REAL", "TEXT"}
#: A mapping from Python types to SQLite types.
SQLITE_TYPES_ALT = {"INT": "INTEGER", "FLOAT": "REAL", "STR": "TEXT"}

#: Mandatory field in the SQLite table used to retrieve a document from its folder.
SQLITE_FOLDER_FIELD = "papis_document_folder"


def _parse_field_from_name(name: str) -> tuple[str, str]:
    """Takes a field name in the form "name:type" (e.g. "author:TEXT") and
    converts it to a string that can be added to a ``CREATE TABLE`` statement.
    """
    if ":" in name:
        name, stype = name.split(":")
    else:
        stype = "TEXT"

    name = name.strip()
    stype = stype.strip().upper()
    stype = SQLITE_TYPES_ALT.get(stype, stype)

    if stype not in SQLITE_ALLOWED_TYPES:
        raise ValueError(f"Field '{name}' has unsupported type '{stype}'")

    return name, stype


@contextmanager
def transaction(conn: sqlite3.Connection, mode: str = "DEFERRED") -> Iterator[None]:
    if mode not in {"DEFERRED", "IMMEDIATE", "EXCLUSIVE"}:
        raise ValueError(f"Unsupported transaction mode '{mode}'")

    conn.execute(f"BEGIN {mode}")
    try:
        yield
    except BaseException:
        conn.rollback()
        raise
    else:
        conn.commit()


class SQLiteDatabase(Database):
    def __init__(self, library: Library | None = None) -> None:
        super().__init__(library)

        from papis.database.base import get_cache_file_name
        from papis.utils import get_cache_home

        self.cache_dir = os.path.join(get_cache_home(), "database", "sqlite")
        self.cache_file_name = os.path.join(
            self.cache_dir,
            f"{get_cache_file_name(self.lib.path_format())}.sqlite")

        self.initialize()

    @cached_property
    def connection(self) -> sqlite3.Connection:
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        logger.debug("Connecting to database at '%s'", self.cache_file_name)

        # https://charlesleifer.com/blog/going-fast-with-sqlite-and-python/
        conn = sqlite3.connect(self.cache_file_name,
                               isolation_level=None)

        # https://github.com/litements/litedict/blob/377603fa597453ffd9997186a493ed4fd23e5399/litedict.py
        conn.execute("PRAGMA journal_mode = 'WAL';")
        conn.execute("PRAGMA temp_store = 'MEMORY';")
        conn.execute("PRAGMA synchronous = 'OFF';")
        conn.execute("PRAGMA cache_size = -64000;")

        return conn

    @cached_property
    def schema_fields(self) -> tuple[str, ...]:
        cursor = self.connection.execute(f"SELECT * FROM {SQLITE_TABLE_NAME}")
        return tuple(field[0] for field in cursor.description if field[0] != "id")

    def get_backend_name(self) -> str:  # noqa: PLR6301
        return "sqlite"

    def get_cache_path(self) -> str:
        return self.cache_file_name

    def get_all_query_string(self) -> str:  # noqa: PLR6301
        return "*"

    def initialize(self) -> None:
        if os.path.exists(self.cache_file_name):
            # TODO: The fields can also differ in "NOT NULL" or some other
            # properties which this doesn't check for. Should it?
            # NOTE: https://www.sqlite.org/pragma.html#pragma_table_info
            db_fields = {
                (field[1], field[2]) for field in self.connection.execute(
                    f"PRAGMA table_info({SQLITE_TABLE_NAME})"
                    ).fetchall() if field[-1] != 1
            } - {(SQLITE_FOLDER_FIELD, "TEXT")}
            user_fields = {
                _parse_field_from_name(name)
                for name in papis.config.getlist("sqlite-schema-fields")
            }

            changed = db_fields != user_fields
        else:
            changed = True

        if changed:
            self.clear()
            self._create_tables()
            self._index_documents()

    def clear(self) -> None:
        # NOTE: this is apparently how cached properties get cleared
        # https://docs.python.org/3/library/functools.html#functools.cached_property
        if "connection" in self.__dict__:
            del self.connection
        if "schema_fields" in self.__dict__:
            del self.schema_fields

        if os.path.exists(self.cache_file_name):
            logger.warning("Clearing database at '%s'...", self.cache_file_name)
            os.remove(self.cache_file_name)

    def add(self, document: Document) -> None:
        from papis.document import describe
        logger.debug("Adding document: '%s'.", describe(document))

        self.maybe_compute_id(document)
        conn = self.connection
        with transaction(conn):
            fields = ", ".join([f":{field}" for field in self.schema_fields])
            conn.execute(
                f"INSERT INTO {SQLITE_TABLE_NAME} VALUES({fields})",
                self._document_as_row(document))

    def update(self, document: Document) -> None:
        from papis.document import describe
        logger.debug("Updating document: '%s'.", describe(document))

        self.maybe_compute_id(document)
        conn = self.connection
        with transaction(conn):
            fields = ", ".join(f"{name} = :{name}" for name in self.schema_fields)
            conn.execute(
                f"UPDATE {SQLITE_TABLE_NAME} "
                f"    SET {fields} "
                "WHERE papis_id = :papis_id",
                self._document_as_row(document))

    def delete(self, document: Document) -> None:
        from papis.document import describe
        logger.debug("Deleting document: '%s'.", describe(document))

        conn = self.connection
        with transaction(conn):
            conn.execute(
                f"DELETE FROM {SQLITE_TABLE_NAME} "
                "WHERE papis_id = :papis_id",
                self._document_as_row(document))

    def query(self, query_string: str) -> list[Document]:
        logger.debug("Querying database for '%s'.", query_string)

        import time

        tstart = time.time()
        conn = self.connection
        with transaction(conn):
            if query_string == self.get_all_query_string():
                results = conn.execute(
                    f"SELECT {SQLITE_FOLDER_FIELD} FROM {SQLITE_TABLE_NAME}"
                ).fetchall()
            else:
                results = conn.execute(
                    f"SELECT {SQLITE_FOLDER_FIELD}, bm25({SQLITE_TABLE_NAME}) AS rank "
                    f"FROM {SQLITE_TABLE_NAME} "
                    f"WHERE {SQLITE_TABLE_NAME} MATCH :query "
                    "ORDER BY rank",
                    {"query": query_string}
                ).fetchall()

        from papis.document import from_folder

        documents = [from_folder(result[0]) for result in results]
        tdelta = 1000 * (time.time() - tstart)
        logger.debug("Finished querying in %.2fms (%d docs).", tdelta, len(documents))

        return documents

    def query_dict(self, query: dict[str, str]) -> list[Document]:
        return self.query(" AND ".join(f'{k}:"{v}"' for k, v in query.items()))

    def get_all_documents(self) -> list[Document]:
        return self.query(self.get_all_query_string())

    def _create_tables(self) -> None:
        if os.path.exists(self.cache_file_name):
            # NOTE: everything already exists, so we can just skip it
            return

        schema_file_name = os.path.join(
            papis.config.get_config_folder(),
            "schema.sqlite")

        if not os.path.exists(schema_file_name):
            from papis.id import ID_KEY_NAME

            field_names = papis.config.getlist("sqlite-schema-fields")
            schema = "\n".join([
                "BEGIN;",
                f"CREATE VIRTUAL TABLE IF NOT EXISTS {SQLITE_TABLE_NAME} USING fts5(",
                f"    {ID_KEY_NAME},",
                f"    {SQLITE_FOLDER_FIELD},",
                *[f"    {name}," for name in field_names],
                ");",
                "COMMIT;\n",
            ])

            with open(schema_file_name, "w", encoding="utf-8") as fd:
                fd.write(schema)
        else:
            with open(schema_file_name, encoding="utf-8") as fd:
                schema = fd.read()

        logger.debug("Creating schema from file '%s'.", schema_file_name)
        conn = self.connection
        with transaction(conn):
            conn.executescript(schema)

    def _document_as_row(self, doc: Document) -> dict[str, str]:
        from papis.document import describe
        from papis.exceptions import DocumentFolderNotFound

        # ensure document has a folder
        folder = doc.get_main_folder()
        if folder is None:
            raise DocumentFolderNotFound(describe(doc))

        # ensure document has a `papis_id`
        self.maybe_compute_id(doc)

        # construct row to add to the database
        # NOTE: the FTS5 virtual table seems to only support TEXT anyway, so we
        # cast all our fields to string here just in case they're not.
        row = {field: str(doc.get(field, "")) for field in self.schema_fields}
        row[SQLITE_FOLDER_FIELD] = folder

        return row

    def _index_documents(self) -> None:
        from itertools import chain

        from papis.utils import folders_to_documents, get_folders

        logger.info("Indexing library. This might take a while...")
        folders: list[str] = list(
            chain.from_iterable(get_folders(d) for d in self.lib.paths)
        )
        documents = folders_to_documents(folders)

        conn = self.connection
        with transaction(conn):
            fields = ", ".join([f":{field}" for field in self.schema_fields])
            conn.executemany(
                f"INSERT INTO {SQLITE_TABLE_NAME} VALUES({fields})",
                [self._document_as_row(doc) for doc in documents])
