"""
Here the database abstraction for the libraries is defined.
"""

import os
import papis.utils
import papis.config


class Database(object):
    """Abstract class for the database backends
    """

    def __init__(self, library=papis.config.get_lib()):
        self.lib = library

    def get_lib(self):
        """Get library name
        """
        return self.lib

    def get_dir(self):
        """Get directory of the library
        """
        return os.path.expanduser(papis.config.get('dir'))

    def match(self, document, query_string):
        """Wether or not document matches query_string

        :param document: Document to be matched
        :type  document: papis.document.Document
        :param query_string: Query string
        :type  query_string: str
        """
        pass

    def clear(self):
        pass

    def add(self, document):
        pass

    def update(self, document):
        pass

    def delete(self, document):
        pass

    def query(self, query_string):
        pass

