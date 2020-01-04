"""
Here the database abstraction for the libraries is defined.
"""

import papis.utils
import papis.config
import papis.library
import papis.document

from typing import Optional, List, Dict, Match
from abc import ABC, abstractmethod


class Database(ABC):
    """Abstract class for the database backends
    """

    def __init__(self, library: Optional[papis.library.Library] = None):
        self.lib = library or papis.config.get_lib()
        assert(isinstance(self.lib, papis.library.Library))

    @abstractmethod
    def initialize(self) -> None:
        ...

    @abstractmethod
    def get_backend_name(self) -> str:
        ...

    def get_lib(self) -> str:
        """Get library name
        """
        return self.lib.name

    def get_dirs(self) -> List[str]:
        """Get directories of the library
        """
        return self.lib.paths

    def match(
            self,
            document: papis.document.Document,
            query_string: str) -> bool:
        """Wether or not document matches query_string

        :param document: Document to be matched
        :type  document: papis.document.Document
        :param query_string: Query string
        :type  query_string: str
        """
        raise NotImplementedError("Match not defined for this class")

    @abstractmethod
    def clear(self) -> None:
        ...

    @abstractmethod
    def add(self, document: papis.document.Document) -> None:
        ...

    @abstractmethod
    def update(self, document: papis.document.Document) -> None:
        ...

    @abstractmethod
    def delete(self, document: papis.document.Document) -> None:
        ...

    @abstractmethod
    def query(self, query_string: str) -> List[papis.document.Document]:
        ...

    @abstractmethod
    def query_dict(self,
            query: Dict[str, str]) -> List[papis.document.Document]:
        ...

    @abstractmethod
    def get_all_documents(self) -> List[papis.document.Document]:
        ...

    @abstractmethod
    def get_all_query_string(self) -> str:
        ...
