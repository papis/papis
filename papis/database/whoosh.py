import whoosh
import papis.config
import papis.database.base
import papis.database.cache

class Database(papis.database.base.Database):

    index = None
    schema = None

    def __init__(self, library=None):
        papis.database.base.Database.__init__(self, library)

    def clear(self):
        whoosh.index.create_in(self.get_index_dir())

    def create_index(self):
        pass

    def create_schema(self):
        from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED
        pass

    def get_index_dir(self):
        return os.path.join(
            papis.database.cache.get_cache_home(),
            'whoosh',
            papis.database.cache.get_name(self.get_dir())
        )

    def get_index_file(self):
        return os.path.join(
            self.get_index_dir(),
            papis.database.cache.get_name(self.get_dir())
        )

