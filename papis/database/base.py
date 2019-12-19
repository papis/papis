"""
Here the database abstraction for the libraries is defined.
"""

import papis.utils
import papis.config
import papis.library


class Database(object):
    """Abstract class for the database backends
    """

    def __init__(self, library=None):
        self.lib = library or papis.config.get_lib()
        assert(isinstance(self.lib, papis.library.Library))

    def initialize(self):
        raise NotImplementedError('Initialize not implemented')

    def get_backend_name(self):
        raise NotImplementedError('Get backend name not implemented')

    def get_lib(self):
        """Get library name
        """
        return self.lib.name

    def get_dirs(self):
        """Get directories of the library
        """
        return self.lib.paths

    def match(self, document, query_string):
        """Wether or not document matches query_string

        :param document: Document to be matched
        :type  document: papis.document.Document
        :param query_string: Query string
        :type  query_string: str
        """
        raise NotImplementedError('Match not implemented')

    def clear(self):
        raise NotImplementedError('Clear not implemented')

    def add(self, document):
        raise NotImplementedError('Add not implemented')

    def update(self, document):
        raise NotImplementedError('Update not implemented')

    def delete(self, document):
        raise NotImplementedError('Delete not implemented')

    def query(self, query_string, sort=None):
        raise NotImplementedError('Query not implemented')

    def query_dict(self, query_string, sort=None):
        raise NotImplementedError('Query dict not implemented')

    def get_all_documents(self, sort=None):
        raise NotImplementedError('Get all docs not implemented')

    def get_all_query_string(self):
        raise NotImplementedError('Get all query string not implemented')

    def sort_field_from_doc(self, doc, field):
        # We want to do a sort that leaves: None last,
        # sorts numbers as numbers and strings as strings.
        # Return a tuple that ensure this.
        value = papis.document.to_dict(doc).get(field, None)

        try:
            int_value = int(value)
            has_int = True
        except ValueError:
            int_value = None
            has_int = False
        except TypeError:
            int_value = None
            has_int = False

        # 'value is None' sorts the documents without
        # the desired field last.
        # 'not has_int' sorts the fields that are not
        # integers after that.
        # 'int_value' sorts on the fields that are integers
        # and has no effect for everything else.
        # 'str(value)' sorts the values that aren't ints.
        return (value is None, not has_int, int_value, str(value))
