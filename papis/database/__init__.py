import logging
logger = logging.getLogger('database')

DATABASES = dict()


def get(library=None):
    global DATABASES
    import papis.config
    backend = papis.config.get('database-backend')
    if library is None:
        library = papis.config.get_lib()
    database = DATABASES.get(library)
    # if there is already a database and the backend of the database
    # is the same as the config backend, then return that library
    # else we will (re)define the database in the dictionary DATABASES
    if database is not None and database.get_backend_name() == backend:
        return DATABASES.get(library)
    if backend == "papis":
        import papis.database.cache
        DATABASES[library] = papis.database.cache.Database(library)
        return DATABASES.get(library)
    elif backend == "whoosh":
        import papis.database.whoosh
        DATABASES[library] = papis.database.whoosh.Database(library)
        return DATABASES.get(library)
    else:
        raise Exception('No valid database type: {}'.format(backend))


def get_all_query_string():
    return get().get_all_query_string()


def clear_cached():
    global DATABASES
    DATABASES = dict()
