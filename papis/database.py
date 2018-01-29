"""
Here the database abstraction for the libraries is defined.
"""

import papis.api
import papis.utils
import papis.config

class Database(object):

    def __init__(self, library=papis.api.get_lib()):
        self.lib = library
        self.documents = []

    def search(self, query_string):
        """Search in the database using a simple query string
        """
        if papis.config.get("database-backend") == "papis":
            if len(self.documents) == 0:
                directory = papis.config.get("dir", section=self.lib)
                self.documents = papis.utils.get_documents(
                    directory, query_string
                )
            return papis.utils.filter_documents(self.documents, query_string)
