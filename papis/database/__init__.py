import papis.config
import papis.exceptions
import logging
logger = logging.getLogger('database')

DATABASES = dict()

def get(library=None):
    import papis.config
    backend = papis.config.get('database-backend')
    if DATABASES.get(library) is not None:
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

