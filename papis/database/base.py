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
        return self.lib

    def get_dir(self):
        return papis.config.get('dir')

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

