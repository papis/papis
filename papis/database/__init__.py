

def get(library=None):
    import papis.config
    if papis.config.get("database-backend") == "papis":
        from papis.cache import Database
        return Database(library)
    elif papis.config.get("database-backend") == "whoosh":
        import papis.database.whoosh
        return papis.database.whoosh.Database(library)

