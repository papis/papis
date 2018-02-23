

def get(library=None):
    import papis.config
    backend = papis.config.get('database-backend')
    if backend == "papis":
        import papis.database.cache
        return papis.database.cache.Database(library)
    elif backend == "whoosh":
        import papis.database.whoosh
        return papis.database.whoosh.Database(library)
    else:
        raise Exception('No valid database type: {}'.format(backend))

