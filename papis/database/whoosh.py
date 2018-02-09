import whoosh
import papis.config
import papis.database.base

class Database(papis.database.base.Database):

    index = None
    schema = None

    def __init__(self, library=None):
        Database.__init__(self, library)

    def clear(self):
        whoosh.index.create_in(self.get_index_dir())

    def create_index(self):
        pass

    def create_schema(self):
        from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED
        pass

    def get_index_dir(self):
        return os.path.join(
            os.path.expanduser(papis.config.get('cache-dir')),
            'whoosh',
            self.get_lib()
        )


