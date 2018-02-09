

def get(library=None):
    import papis.config
    if papis.config.get("database-backend") == "papis":
        import papis.database.cache
        return papis.database.cache.Database(library)
    elif papis.config.get("database-backend") == "whoosh":
        import papis.database.whoosh
        return papis.database.whoosh.Database(library)

