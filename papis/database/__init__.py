
import papis.config

def get():
    if papis.config.get("database-backend") == "papis":
        import papis.cache
        return papis.cache.Database()
    elif papis.config.get("database-backend") == "whoosh":
        import papis.database.whoosh
        return papis.database.whoosh.Databse()

