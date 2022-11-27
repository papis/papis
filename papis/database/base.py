"""
Here the database abstraction for the libraries is defined.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict

import papis.utils
import papis.config
import papis.library
import papis.document


class Database(ABC):
    """Abstract class for the database backends
    """

    def __init__(self, library: Optional[papis.library.Library] = None) -> None:
        self.lib = library or papis.config.get_lib()
        assert isinstance(self.lib, papis.library.Library)

    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def get_backend_name(self) -> str:
        pass

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
        """
        Whether or not document matches query_string.

        :param document: Document to be matched
        :param query_string: Query string
        """
        raise NotImplementedError("Match not defined for this class")

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def add(self, document: papis.document.Document) -> None:
        pass

    @abstractmethod
    def update(self, document: papis.document.Document) -> None:
        pass

    @abstractmethod
    def delete(self, document: papis.document.Document) -> None:
        pass

    @abstractmethod
    def query(self, query_string: str) -> List[papis.document.Document]:
        pass

    @abstractmethod
    def query_dict(
            self, query: Dict[str, str]) -> List[papis.document.Document]:
        pass

    @abstractmethod
    def get_all_documents(self) -> List[papis.document.Document]:
        pass

    @abstractmethod
    def get_all_query_string(self) -> str:
        pass
