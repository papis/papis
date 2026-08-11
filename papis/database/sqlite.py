from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from contextlib import contextmanager
from functools import cached_property
from typing import TYPE_CHECKING, Any

import papis.config
import papis.logging
from papis.database.base import Database

if TYPE_CHECKING:
    from collections.abc import Collection, Iterator, Sequence

    from papis.document import Document
    from papis.library import Library

logger = papis.logging.get_logger(__name__)

#: The name of the table used in the SQLite database.
SQLITE_TABLE_NAME = "documents"

#: A set of reserved columns that cannot be provided in :confval:`sqlite-schema-fields`.
SQLITE_RESERVED_COLUMNS = frozenset({"id", "papis_id", "doc_folder", "doc"})

#: A regex used to determine valid field names. This should include all key names
#: used by Papis documents.
SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _get_sqlite_fields(dbfile: str) -> list[str]:
    # NOTE: https://www.sqlite.org/pragma.html#pragma_table_xinfo
    # NOTE: creating a temporary connection to check fields

    conn = sqlite3.connect(dbfile, isolation_level=None)
    db_fields = [
        field[0] for field in
        conn.execute(
            f"SELECT name FROM pragma_table_xinfo('{SQLITE_TABLE_NAME}') "
            "WHERE hidden = 2"
        ).fetchall()
    ]
    conn.close()

    return db_fields


def _get_sqlite_schema_fields() -> list[str]:
    fields = [
        *papis.config.getlist("sqlite-schema-fields"),
        *papis.config.getlist("sqlite-schema-fields-extend")
    ]

    return sorted(set(fields))


def _make_sqlite_schema(table: str, columns: Sequence[str]) -> str:
    # NOTE: some design choices here:
    # - Storing the whole document in the `doc` field as JSON so that we don't have
    #   to load it from disk every time (like the whoosh backend is doing).
    # - Adding FTS so that we have a bit more flexibility searching.
    # - `papis_id` is not set as the PRIMARY KEY because FTS does not support
    #   non-integer rowids.
    # - Need the TRIGGER complexity because FTS does not support these
    #   GENERATED VIRTUAL columns, so we manually keep them in sync.
    # - A fixed number of searchable columns (see :confval:`sqlite-schema-fields`).

    # NOTE: inspiration:
    #   https://www.dbpro.app/blog/sqlite-json-virtual-columns-indexing

    if any(name in SQLITE_RESERVED_COLUMNS for name in columns):
        raise ValueError(
            f"one of the field names is reserved: {columns} "
            f"(reserved names {SQLITE_RESERVED_COLUMNS})")

    if any(not SAFE_IDENTIFIER_RE.match(name) for name in columns):
        raise ValueError(
            f"columns have invalid (non-alphanumeric) names: {columns}"
        )

    columns_generated_virtual = ",\n    ".join(
        f"{name} TEXT GENERATED ALWAYS AS (json_extract(doc, '$.{name}')) VIRTUAL"
        for name in columns
    )

    columns = ["papis_id", *columns]
    column_names = ", ".join(name for name in columns)
    column_new_names = ", ".join(f"new.{name}" for name in columns)
    column_old_names = ", ".join(f"old.{name}" for name in columns)

    schema = "\n".join([
        "BEGIN;",
        f"CREATE TABLE IF NOT EXISTS {table} (",
        "    id INTEGER PRIMARY KEY,",
        "    papis_id TEXT UNIQUE NOT NULL,",
        "    doc_folder TEXT NOT NULL,",
        "    doc JSON NOT NULL,",
        f"    {columns_generated_virtual}",
        ");",
        "",
        f"CREATE VIRTUAL TABLE {table}_fts USING fts5(",
        f"    {column_names},",
        f"    content='{table}',",
        "    content_rowid='id'",
        ");",
        "",
        f"CREATE TRIGGER {table}_fts_insert AFTER INSERT ON {table} BEGIN",
        f"    INSERT INTO {table}_fts(rowid, {column_names})",
        f"           VALUES (new.id, {column_new_names});",
        "END;",
        "",
        f"CREATE TRIGGER {table}_fts_delete AFTER DELETE ON {table} BEGIN",
        f"    INSERT INTO {table}_fts({table}_fts, rowid, {column_names})",
        f"           VALUES ('delete', old.id, {column_old_names});",
        "END;",
        "",
        f"CREATE TRIGGER {table}_fts_update AFTER UPDATE ON {table} BEGIN",
        f"    INSERT INTO {table}_fts({table}_fts, rowid, {column_names})",
        f"           VALUES ('delete', old.id, {column_old_names});",
        f"    INSERT INTO {table}_fts(rowid, {column_names})",
        f"           VALUES (new.id, {column_new_names});",
        "END;",
    ])
    logger.debug("Schema:\n%s", schema)

    return schema


@contextmanager
def transaction(conn: sqlite3.Connection, mode: str = "DEFERRED") -> Iterator[None]:
    if mode not in {"DEFERRED", "IMMEDIATE", "EXCLUSIVE"}:
        raise ValueError(f"Unsupported transaction mode '{mode}'")

    conn.execute(f"BEGIN {mode}")
    try:
        yield
    except BaseException as exc:
        logger.error("Failed transaction. Rolling back...", exc_info=exc)
        conn.rollback()
    else:
        conn.commit()


class JSONEncoder(json.JSONEncoder):
    def default(self, obj: object) -> Any:
        import datetime

        # NOTE: this is needed because PyYAML automatically transforms ISO dates to
        # a `datetime.date` object, which the JSON encoder does not natively support.
        if isinstance(obj, datetime.date):
            return obj.isoformat()

        return super().default(obj)


def _docs_from_rows(rows: Sequence[tuple[str, ...]]) -> list[Document]:
    """Materialize :class:`~papis.document.Document` objects from rows.

    :param rows: ``(doc_folder, doc, ...)`` tuples as returned by
        ``SELECT doc_folder, doc ...`` queries.
    """
    from papis.document import from_data

    documents: list[Document] = []
    for doc_folder, doc_json, *_ in rows:
        doc = from_data(json.loads(doc_json))
        doc.set_folder(doc_folder)
        documents.append(doc)
    return documents


class SQLiteDatabase(Database):
    def __init__(self, library: Library | None = None) -> None:
        super().__init__(library)

        from papis.database.base import get_cache_file_name
        from papis.utils import get_cache_home

        self.cache_dir = os.path.join(get_cache_home(), "database", "sqlite")
        self.cache_file_name = os.path.join(
            self.cache_dir,
            f"{get_cache_file_name(self.lib.path)}.sqlite")

        self.initialize()

    @cached_property
    def connection(self) -> sqlite3.Connection:
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        logger.debug("Connecting to database at '%s'", self.cache_file_name)

        # https://charlesleifer.com/blog/going-fast-with-sqlite-and-python/
        conn = sqlite3.connect(self.cache_file_name, isolation_level=None)

        # https://github.com/litements/litedict/blob/377603fa597453ffd9997186a493ed4fd23e5399/litedict.py
        # NOTE: setting 'synchronous = OFF' can corrupt the database on a crash,
        # but it's pretty easy to regenerate it in our case, so hopefully ok
        conn.execute("PRAGMA journal_mode = 'WAL';")
        conn.execute("PRAGMA temp_store = 'MEMORY';")
        conn.execute("PRAGMA synchronous = 'OFF';")
        conn.execute("PRAGMA cache_size = -64000;")

        return conn

    def _finalize_connection(self) -> None:
        if "connection" in self.__dict__:
            try:
                # NOTE: ensure that the WAL files are written back
                self.connection.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            except Exception:
                pass

            self.connection.commit()
            self.connection.close()

    # FIXME: __del__ is not very reliable, but hopefully it gets called eventually,
    # e.g. on program exit something. Will need to have a better db handling..
    def __del__(self) -> None:
        self._finalize_connection()

    def get_backend_name(self) -> str:  # ruff:ignore[no-self-use]
        return "sqlite"

    def get_cache_path(self) -> str:
        return self.cache_file_name

    def get_all_query_string(self) -> str:  # ruff:ignore[no-self-use]
        return "*"

    def initialize(self) -> None:
        if os.path.exists(self.cache_file_name):
            changed = (
                set(_get_sqlite_fields(self.get_cache_path()))
                != set(_get_sqlite_schema_fields()))
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
            self._finalize_connection()
            del self.connection

        if os.path.exists(self.cache_file_name):
            logger.warning("Clearing database at '%s'...", self.cache_file_name)

            # NOTE: remove all files related to this database
            for suffix in ("", "-wal", "-shm"):
                filename = f"{self.cache_file_name}{suffix}"
                if os.path.exists(filename):
                    os.remove(filename)

    def add(self, doc: Document) -> None:
        from papis.document import describe
        logger.debug("Adding document: '%s'.", describe(doc))

        folder = doc.get_main_folder()
        if folder is None:
            from papis.exceptions import DocumentFolderNotFound
            raise DocumentFolderNotFound(describe(doc))

        conn = self.connection
        with transaction(conn):
            conn.execute(
                f"INSERT INTO {SQLITE_TABLE_NAME}(papis_id, doc_folder, doc) "
                    "VALUES(?, ?, ?)",
                (self.maybe_compute_id(doc),
                 folder,
                 json.dumps(doc, cls=JSONEncoder)))

    def update(self, doc: Document) -> None:
        from papis.document import describe
        logger.debug("Updating document: '%s'.", describe(doc))

        folder = doc.get_main_folder()
        if folder is None:
            from papis.exceptions import DocumentFolderNotFound
            raise DocumentFolderNotFound(describe(doc))

        conn = self.connection
        with transaction(conn):
            conn.execute(
                f"UPDATE {SQLITE_TABLE_NAME} "
                "    SET doc_folder = ?, doc = ?"
                "WHERE papis_id = ?",
                (folder,
                 json.dumps(doc, cls=JSONEncoder),
                 self.maybe_compute_id(doc)))

    def delete(self, doc: Document) -> None:
        from papis.document import describe
        logger.debug("Deleting document: '%s'.", describe(doc))

        conn = self.connection
        with transaction(conn):
            cursor = conn.execute(
                f"DELETE FROM {SQLITE_TABLE_NAME} WHERE papis_id = ?",
                (self.maybe_compute_id(doc),))

        if cursor.rowcount == 0:
            from papis.exceptions import DocumentFolderNotFound
            raise DocumentFolderNotFound(describe(doc))

    def query(self, query_string: str) -> list[Document]:
        logger.debug("Querying database for '%s'.", query_string)

        tstart = time.time()
        conn = self.connection
        if query_string == self.get_all_query_string():
            results = conn.execute(
                f"SELECT doc_folder, doc FROM {SQLITE_TABLE_NAME}"
            ).fetchall()
        else:
            try:
                table = SQLITE_TABLE_NAME
                results = conn.execute(
                    f"SELECT doc_folder, doc, bm25({table}_fts) AS rank "
                    f"FROM {table} "
                    f"JOIN {table}_fts "
                    f"ON {table}.papis_id = {table}_fts.papis_id "
                    f"WHERE {table}_fts MATCH ? ORDER BY rank",
                    (query_string,)
                ).fetchall()
            except sqlite3.OperationalError as exc:
                logger.error("Failed to query for '%s'.", query_string, exc_info=exc)
                results = []

        documents = _docs_from_rows(results)

        tdelta = 1000 * (time.time() - tstart)
        logger.debug("Finished querying in %.2fms (%d docs).", tdelta, len(documents))

        return documents

    def query_dict(self, query: dict[str, str]) -> list[Document]:
        return self.query(" AND ".join(f'{k}:"{v}"' for k, v in query.items()))

    def get_all_documents(self) -> list[Document]:
        return self.query(self.get_all_query_string())

    def query_paged(
        self,
        query: str,
        *,
        folder: str | None = None,
        ids: Collection[str] | None = None,
        sort: str | None = None,
        reverse: bool | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[Document], int]:
        from pathlib import Path

        sort, reverse = self._resolve_sort(query, sort, reverse)

        table = SQLITE_TABLE_NAME
        joins: list[str] = []
        clauses: list[str] = []
        params: dict[str, object] = {}
        if query != self.get_all_query_string():
            joins.append(
                f"JOIN {table}_fts ON {table}.papis_id = {table}_fts.papis_id"
            )
            clauses.append(f"{table}_fts MATCH :query")
            params["query"] = query

        if folder is not None:
            abs_prefix = str(Path(self.lib.path) / folder)
            # check if doc_folder is equal to or subfolder of *folder*
            clauses.append(
                f"({table}.doc_folder = :folder"
                f" OR instr({table}.doc_folder, :folder || '/') = 1)"
            )
            params["folder"] = abs_prefix

        if ids is not None:
            placeholders = ", ".join(f":id{i}" for i in range(len(ids)))
            clauses.append(f"{table}.papis_id IN ({placeholders})")
            params.update({f"id{i}": v for i, v in enumerate(ids)})

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        if sort is not None:
            direction = "DESC" if reverse else "ASC"
            params["path"] = f"$.{sort}"
            # NOTE: sorting by an arbitrary metadata key always requires a full table
            # scan. If it ever becomes a bottleneck, index the generated
            # ``sqlite-schema-fields`` columns and order by the column name.
            order_by = (
                f"ORDER BY json_extract({table}.doc, :path) IS NULL,"
                f" json_extract({table}.doc, :path) {direction}"
            )
        elif query != self.get_all_query_string():
            order_by = f"ORDER BY bm25({table}_fts)"
        else:
            order_by = ""

        params["limit"] = -1 if limit is None else limit
        params["offset"] = offset

        join_clauses = " ".join(joins)
        try:
            rows = self.connection.execute(
                f"SELECT {table}.doc_folder, {table}.doc"
                f" FROM {table} {join_clauses} {where} {order_by}"
                f" LIMIT :limit OFFSET :offset",
                params,
            ).fetchall()

            total = self.connection.execute(
                f"SELECT COUNT(*) FROM {table} {join_clauses} {where}",
                params,
            ).fetchone()[0]
        except sqlite3.OperationalError as exc:
            logger.error(
                "Failed to query for '%s'.", query, exc_info=exc,
            )
            return [], 0

        return _docs_from_rows(rows), total

    def find_by_folder(self, folder: str) -> Document | None:
        conn = self.connection
        results = conn.execute(
            f"SELECT doc_folder, doc FROM {SQLITE_TABLE_NAME} "
            "WHERE doc_folder = ?",
            (folder,),
        ).fetchall()

        if not results:
            return None

        return _docs_from_rows(results[:1])[0]

    def _create_tables(self) -> None:
        if os.path.exists(self.cache_file_name):
            # NOTE: everything already exists, so we can just skip it
            return

        schema = _make_sqlite_schema(SQLITE_TABLE_NAME, _get_sqlite_schema_fields())

        conn = self.connection
        conn.executescript(schema)
        conn.commit()

    def _index_documents(self) -> None:
        from papis.utils import folders_to_documents, get_folders

        logger.info("Indexing library. This might take a while...")
        folders = get_folders(self.lib.path)
        documents = folders_to_documents(folders)

        from papis.document import describe

        conn = self.connection
        with transaction(conn):
            # NOTE: we need to insert these one-by-one because `maybe_compute_id`
            # also queries the database to ensure the ids are unique..
            for doc in documents:
                papis_id = self.maybe_compute_id(doc)
                folder = doc.get_main_folder()
                if folder is None:
                    logger.error("Cannot index a document without a folder: '%s'.",
                                 describe(doc))
                    continue

                conn.execute(
                    f"INSERT INTO {SQLITE_TABLE_NAME}(papis_id, doc_folder, doc) "
                        "VALUES(?, ?, ?)",
                    (papis_id, folder, json.dumps(doc, cls=JSONEncoder))
                )
