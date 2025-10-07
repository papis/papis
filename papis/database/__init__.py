from typing import TYPE_CHECKING

import papis.config
import papis.logging

if TYPE_CHECKING:
    import papis.library
    from papis.database.base import Database

logger = papis.logging.get_logger(__name__)

DATABASES: dict["papis.library.Library", "Database"] = {}


def _instantiate_database(backend_name: str,
                          library: "papis.library.Library") -> "Database":
    if backend_name == "papis":
        from papis.database.cache import PickleDatabase
        return PickleDatabase(library)
    elif backend_name == "whoosh":
        from papis.database.whoosh import WhooshDatabase
        return WhooshDatabase(library)
    else:
        raise ValueError(f"Invalid database backend: '{backend_name}'")


def get_database(library_name: str | None = None) -> "Database":
    """Get the database for the library *library_name*.

    If *library_name* is *None*, then the current database is retrieved from
    :func:`papis.config.get_lib`. The given library name must exist in the
    configuration file or it should be a path to a directory containing Papis
    documents (see :func:`papis.config.get_lib_from_name`).

    :return: the caching database for the given library. The same database is
        returned on repeated calls to this function.
    """
    if library_name is None:
        library = papis.config.get_lib()
    else:
        library = papis.config.get_lib_from_name(library_name)

    backend = papis.config.getstring("database-backend") or "papis"
    try:
        database = DATABASES[library]
    except KeyError:
        database = _instantiate_database(backend, library)
        DATABASES[library] = database

    return database


def get(library_name: str | None = None) -> "Database":
    return get_database(library_name)


def get_all_query_string() -> str:
    """Get the default query string for the current database."""
    return get().get_all_query_string()


def clear_cached() -> None:
    """Clear cached databases.

    After this function is called, all subsequent calls to :func:`get` will
    recreate the database for the given library.
    """
    DATABASES.clear()
