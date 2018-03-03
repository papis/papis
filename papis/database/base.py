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

    def initialize(self):
        pass

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
        raise NotImplementedError('Clear not implemented')

    def add(self, document):
        raise NotImplementedError('Add not implemented')

    def update(self, document):
        raise NotImplementedError('Update not implemented')

    def delete(self, document):
        raise NotImplementedError('Delete not implemented')

    def query(self, query_string):
        raise NotImplementedError('Query not implemented')

    def get_all_documents(self):
        raise NotImplementedError('Get all docs not implemented')
