"""
This module describes which functions are intended to be used by users to
create papis scripts.

.. class:: T
"""

from typing import Any, Callable, Dict, List, Optional, Sequence, TypeVar, Union

import papis.utils
import papis.config
import papis.document
import papis.logging

logger = papis.logging.get_logger(__name__)

T = TypeVar("T")


def get_lib_name() -> str:
    """
    Get current library.

    It either retrieves the library from the environment ``PAPIS_LIB`` variable,
    the command-line arguments passed in by the user or the configuration
    files.

    :returns: the name of the library.

    >>> get_lib_name() is not None
    True
    """
    return papis.config.get_lib_name()


def set_lib_from_name(library: str) -> None:
    """
    Set current library.

    It either sets the library from the environment ``PAPIS_LIB`` variable,
    the command-line args passed by the user or the configuration files.

    :param library: name of a library (as defined in the configuration files)
        or a path to an existing library.
    """
    papis.config.set_lib_from_name(library)


def get_libraries() -> List[str]:
    """
    Get all the libraries declared in the configuration files.

    A library in the configuration files is a section that has the ``dir``
    or ``dirs`` keys defined.

    :returns: a :class:`list` of library names.

    >>> len(get_libraries()) >= 1
    True
    """
    return papis.config.get_libs()


def pick_doc(
        documents: Sequence[papis.document.Document],
        ) -> Sequence[papis.document.Document]:
    """
    Pick a subset of documents from the given *documents*.

    :param documents: a sequence of documents.
    :returns: a subset of *documents* corresponding to the user selected ones.
    """
    import papis.pick

    return papis.pick.pick_doc(documents)


def pick(items: Sequence[T],
         default_index: int = 0,
         header_filter: Optional[Callable[[T], str]] = None,
         match_filter: Optional[Callable[[T], str]] = None) -> Sequence[T]:
    """
    Pick a subset of items from the given *items*.

    :param items: a sequence of items.
    :param default_index: index used when no explicit item is picked.
    :param header_filter: a callable to stringify the given item for display.
    :param match_filter: a callable to stringify the given item for display.
    """
    import papis.pick

    if header_filter is None:
        header_filter = str

    if match_filter is None:
        match_filter = str

    return papis.pick.pick(
        items,
        default_index=default_index,
        header_filter=header_filter,
        match_filter=match_filter)


def open_file(file_path: str, wait: bool = True) -> None:
    """
    Open the given file using the configured ``opentool``.

    :param file_path: a path to a file.
    :param wait: if *True*, wait for the completion of the opener program
        before continuing execution (blocking behavior).
    """
    papis.utils.open_file(file_path, wait=wait)


def open_dir(dir_path: str, wait: bool = True) -> None:
    """
    Open the given directory using the configured ``file-browser``.

    :param dir_path: a path to a folder.
    :param wait: if *True*, wait for the completion of the opener program
        before continuing execution (blocking behavior).
    """
    papis.utils.general_open(dir_path, "file-browser", wait=wait)


def edit_file(file_path: str, wait: bool = True) -> None:
    """
    Edit the given file using the configured ``editor``.

    :param file_path: a path to a file.
    :param wait: if *True*, wait for the completion of the editor before
        continuing execution (blocking behavior).
    """
    papis.utils.general_open(file_path, "editor", wait=wait)


def get_all_documents_in_lib(
        library: Optional[str] = None) -> List[papis.document.Document]:
    """
    Get *all* documents in the given library.

    :param library: a library name.
    :returns: a :class:`list` of all known documents in the library.

    >>> import tempfile
    >>> folder = tempfile.mkdtemp()
    >>> set_lib_from_name(folder)
    >>> docs = get_all_documents_in_lib(folder)
    >>> len(docs)
    0
    """
    import papis.database
    return papis.database.get(library).get_all_documents()


def get_documents_in_dir(
        directory: str,
        search: str = "") -> List[papis.document.Document]:
    """
    Get documents contained in the given folder.

    :param directory: a path to a folder containing documents.
    :param search: a search string used to filter the documents.
    :returns: a :class:`list` of filtered documents from *directory*.

    >>> import tempfile
    >>> docs = get_documents_in_dir(tempfile.mkdtemp())
    >>> len(docs)
    0
    """
    set_lib_from_name(directory)
    return get_documents_in_lib(directory, search)


def get_documents_in_lib(
        library: Optional[str] = None,
        search: Union[Dict[str, Any], str] = "") -> List[papis.document.Document]:
    """
    Get documents contained in the given library.

    :param library: a library name.
    :param search: a search parameter used to filter the documents.
    :returns: a :class:`list` of filtered documents from *library*.
    """
    import papis.database
    db = papis.database.get(library)

    if isinstance(search, str):
        return db.query(search)
    elif isinstance(search, dict):
        return db.query_dict(search)
    else:
        raise TypeError("Unknown search parameter: '{}'".format(search))


def clear_lib_cache(lib: Optional[str] = None) -> None:
    """
    Clear the cache associated with a library.

    If no library is given, then the current library is used.

    :param lib: a library name.

    >>> clear_lib_cache()
    """
    import papis.database
    papis.database.get(lib).clear()


def doi_to_data(doi: str) -> Dict[str, Any]:
    """
    Get metadata for the given *doi* by querying
    `Crossref <https://www.crossref.org/>`__.

    :param doi: a valid DOI (Document Object Identifier).
    :returns: metadata for the given identifier.
    """
    import papis.crossref
    return papis.crossref.doi_to_data(doi)


def save_doc(doc: papis.document.Document) -> None:
    """
    Save the document to disk.

    This commits the new document to the database and saves it to disk
    by updating its *info.yaml* file.

    :param doc: an existing document.
    """
    import papis.database

    db = papis.database.get()
    doc.save()
    db.update(doc)
