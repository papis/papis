"""
Here the database abstraction for the libraries is defined.
"""

import papis.api
import papis.utils
import papis.config

class Database(object):

    def __init__(self, library=papis.api.get_lib()):
        self.lib = library

    def search(self, query_string):
        """Search in the database using a simple query string
        """
        if papis.config.get("database-backend") == "papis":
            directory = papis.config.get("dir", section=self.lib)
            return papis.utils.get_documents(directory, query_string)
