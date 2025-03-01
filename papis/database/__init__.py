from typing import Optional, Dict

from .base import Database
from papis.library import Library
import papis.logging

logger = papis.logging.get_logger(__name__)

DATABASES: Dict[Library, Database] = {}


def get(library_name: Optional[str] = None) -> Database:
    import papis.config

    if library_name is None:
        library = papis.config.get_lib()
    else:
        library = papis.config.get_lib_from_name(library_name)

    backend = papis.config.get("database-backend") or "papis"

    try:
        database = DATABASES[library]
    except KeyError:
        database = _instantiate_database(backend, library)
        DATABASES[library] = database

    return database


def _instantiate_database(backend_name: str, library: Library) -> Database:
    if backend_name == "papis":
        import papis.database.cache
        return papis.database.cache.Database(library)
    elif backend_name == "whoosh":
        import papis.database.whoosh
        return papis.database.whoosh.Database(library)
    else:
        raise ValueError(f"Invalid database backend: '{backend_name}'")


def get_all_query_string() -> str:
    return get().get_all_query_string()


def clear_cached() -> None:
    global DATABASES
    DATABASES = {}
