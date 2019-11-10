"""
Here the database abstraction for the libraries is defined.
"""

import papis.utils
import papis.config
import papis.library
import papis.document

from typing import Optional, List, Dict, Match


class Database(object):
    """Abstract class for the database backends
    """

    def __init__(self, library: Optional[papis.library.Library] = None):
        self.lib = library or papis.config.get_lib()
        assert(isinstance(self.lib, papis.library.Library))

    def initialize(self) -> None:
        raise NotImplementedError('Initialize not implemented')

    def get_backend_name(self) -> str:
        raise NotImplementedError('Get backend name not implemented')

    def get_lib(self) -> str:
        """Get library name
        """
        return self.lib.name

    def get_dirs(self) -> List[str]:
        """Get directories of the library
        """
        return self.lib.paths

    def match(self, document: papis.document.Document,
            query_string: str) -> bool:
        """Wether or not document matches query_string

        :param document: Document to be matched
        :type  document: papis.document.Document
        :param query_string: Query string
        :type  query_string: str
        """
        raise NotImplementedError('Match not implemented')

    def clear(self) -> None:
        raise NotImplementedError('Clear not implemented')

    def add(self, document: papis.document.Document) -> None:
        raise NotImplementedError('Add not implemented')

    def update(self, document: papis.document.Document) -> None:
        raise NotImplementedError('Update not implemented')

    def delete(self, document: papis.document.Document) -> None:
        raise NotImplementedError('Delete not implemented')

    def query(self, query_string: str) -> List[papis.document.Document]:
        raise NotImplementedError('Query not implemented')

    def query_dict(self, query: Dict[str, str]
            ) -> List[papis.document.Document]:
        raise NotImplementedError('Query dict not implemented')

    def get_all_documents(self) -> List[papis.document.Document]:
        raise NotImplementedError('Get all docs not implemented')

    def get_all_query_string(self) -> str:
        raise NotImplementedError('Get all query string not implemented')
