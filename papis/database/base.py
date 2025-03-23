import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from warnings import warn

from papis.document import Document
from papis.library import Library


def get_cache_file_name(libpaths: str) -> str:
    """Create a cache file name out of the path of a given directory.

    :param libpaths: folder names to be used as a seed for the cache name.
    :returns: a name for the cache file specific to *libpaths*.

    >>> get_cache_file_name('path/to/my/lib')
    'a8c689820a94babec20c5d6269c7d488-lib'
    >>> get_cache_file_name('papers')
    'a566b2bebc62611dff4cdaceac1a7bbd-papers'
    """
    import hashlib
    return "{}-{}".format(
        hashlib.md5(libpaths.encode()).hexdigest(),
        os.path.basename(libpaths))


def get_cache_file_path(libpaths: str) -> str:
    """Get the full path to the cache file.

    :param libpaths: a cache file specific for the given library paths.
    """
    from papis.utils import get_cache_home

    cache_name = get_cache_file_name(libpaths)
    folder = os.path.join(get_cache_home(), "database")
    if not os.path.exists(folder):
        os.makedirs(folder)

    return os.path.join(folder, cache_name)


class Database(ABC):
    """Abstract base class for Papis caching database backends."""

    def __init__(self, library: Optional[Library] = None) -> None:
        if library is None:
            from papis.config import get_lib
            library = get_lib()

        if not isinstance(library, Library):
            raise TypeError(f"Provided library has unsupported type: {type(library)}")

        self.lib = library

    @abstractmethod
    def get_backend_name(self) -> str:
        """Get the name of the database backend.

        This name has to match the one used in the configuration file in the
        :confval:`database-backend` setting.
        """

    @abstractmethod
    def get_cache_path(self) -> str:
        """Get the path to the database cache file (or directory)."""

    @abstractmethod
    def get_all_query_string(self) -> str:
        """Get the default query string that will match all documents."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the caching database backend.

        This can involve creating any necessary directories, opening files, etc.
        This function should be called in the constructor of the database class,
        as needed.
        """

    @abstractmethod
    def clear(self) -> None:
        """Clear the database by removing all files and directories.

        After clearing the database, calling :meth:`initialize` may be necessary
        to ensure that it is in the correct state.
        """

    @abstractmethod
    def add(self, document: Document) -> None:
        """Add a new document to the database."""

    @abstractmethod
    def update(self, document: Document) -> None:
        """Replace an existing document in the database."""

    @abstractmethod
    def delete(self, document: Document) -> None:
        """Remove a document from the database."""

    @abstractmethod
    def query(self, query_string: str) -> List[Document]:
        """Find a document in the database by the given *query_string*.

        The query string can have a more complex syntax based on the database
        backend.
        """

    @abstractmethod
    def query_dict(self, query: Dict[str, str]) -> List[Document]:
        """Find a document in the database that matches the keys in *query*."""

    @abstractmethod
    def get_all_documents(self) -> List[Document]:
        """Get all documents in the database."""

    def find_by_id(self, identifier: str) -> Optional[Document]:
        """Find a document in the library by its Papis ID *identifier*."""
        from papis.id import ID_KEY_NAME

        results = self.query_dict({ID_KEY_NAME: identifier})
        if len(results) > 1:
            raise ValueError(f"More than one document matches the ID '{identifier}'")

        return results[0] if results else None

    def maybe_compute_id(self, doc: Document) -> None:
        """Compute a Papis ID for the document *doc*.

        If the document already has an ID, then the document is skipped and the
        ID is not checked for duplicates. Otherwise a new unique ID is created
        and the document :ref:`info-file` is updated accordingly.
        """
        from papis.id import ID_KEY_NAME, compute_an_id

        if ID_KEY_NAME in doc:
            return

        # NOTE: `compute_an_id` adds a random seed to the ID, so this is quite
        # unlikely to become an infinite loop
        new_id = compute_an_id(doc)
        while self.query_dict({ID_KEY_NAME: new_id}):
            new_id = compute_an_id(doc)

        # FIXME: Should this save the document?
        doc[ID_KEY_NAME] = new_id
        doc.save()

    def get_lib(self) -> str:
        warn(f"Calling '{type(self).__name__}.get_lib' directly is deprecated "
             "and will be removed in the next version of Papis (after 0.15). Use "
             "the 'self.lib.name' member directly.",
             DeprecationWarning, stacklevel=2)

        return self.lib.name

    def get_dirs(self) -> List[str]:
        warn(f"Calling '{type(self).__name__}.get_dirs' directly is deprecated "
             "and will be removed in the next version of Papis (after 0.15). Use "
             "the 'self.lib.paths' member directly.",
             DeprecationWarning, stacklevel=2)

        return self.lib.paths

    @staticmethod
    def get_id_key() -> str:
        from warnings import warn

        warn("This function is deprecated and will be removed in the next "
             "version of Papis (after 0.15). Use 'papis.id.ID_KEY_NAME' instead.",
             DeprecationWarning, stacklevel=2)

        from papis.id import ID_KEY_NAME
        return ID_KEY_NAME
