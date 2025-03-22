"""
Here the database abstraction for the libraries is defined.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict

import papis.utils
import papis.config
import papis.library
import papis.document
import papis.id


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

    def get_cache_path(self) -> str:
        """Get the path to the actual cache file or directory.
        """
        raise NotImplementedError(
            f"Cache path not defined for backend '{self.get_backend_name()}'")

    def match(
            self,
            document: papis.document.Document,
            query_string: str) -> bool:
        """
        Whether or not document matches query_string.

        :param document: Document to be matched
        :param query_string: Query string
        """
        raise NotImplementedError(
            f"Match not defined for backend '{self.get_backend_name()}'")

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

    def find_by_id(self, identifier: str) -> Optional[papis.document.Document]:
        results = self.query_dict({Database.get_id_key(): identifier})
        if len(results) > 1:
            raise ValueError(
                f"More than one document matches the unique id '{identifier}'")

        return results[0] if results else None

    @staticmethod
    def get_id_key() -> str:
        """
        Get the unique key identifier name of the documents in the database
        """
        return papis.id.key_name()

    def maybe_compute_id(self, doc: papis.document.Document) -> None:
        """
        Compute a Papis ID for the document doc.

        If the document already has an ID, then the document is skipped (without
        checking for duplicates). Otherwise try to create a new ID that is
        unique in this database and update the document YAML accordingly.
        """
        key_name = papis.id.key_name()
        if key_name in doc:
            return
        while True:
            new_id = papis.id.compute_an_id(doc)
            other_docs = self.query_dict({key_name: new_id})
            if not other_docs:
                break
        doc[key_name] = new_id
        doc.save()
