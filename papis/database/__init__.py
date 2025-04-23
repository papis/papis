from typing import Optional, Dict

from .base import Database
from papis.library import Library
import papis.logging

logger = papis.logging.get_logger(__name__)

DATABASES: Dict[Library, Database] = {}


def _instantiate_database(backend_name: str, library: Library) -> Database:
    if backend_name == "papis":
        import papis.database.cache
        return papis.database.cache.Database(library)
    elif backend_name == "whoosh":
        import papis.database.whoosh
        return papis.database.whoosh.Database(library)
    else:
        raise ValueError(f"Invalid database backend: '{backend_name}'")


def get(library_name: Optional[str] = None) -> Database:
    """Get the database for the library *library_name*.

    If *library_name* is *None*, then the current database is retrieved from
    :func:`papis.config.get_lib`. The given library name must exist in the
    configuration file or it should be a path to a directory containing Papis
    documents (see :func:`papis.config.get_lib_from_name`).

    :return: the caching database for the given library. The same database is
        returned on repeated calls to this function.
    """
    from papis.config import get_lib, get_lib_from_name

    if library_name is None:
        library = get_lib()
    else:
        library = get_lib_from_name(library_name)

    backend = papis.config.getstring("database-backend") or "papis"
    try:
        database = DATABASES[library]
    except KeyError:
        database = _instantiate_database(backend, library)
        DATABASES[library] = database

    return database


def get_all_query_string() -> str:
    """Get the default query string for the current database."""
    return get().get_all_query_string()


def clear_cached() -> None:
    """Clear cached databases.

    After this function is called, all subsequent calls to :func:`get` will
    recreate the database for the given library.
    """
    DATABASES.clear()
