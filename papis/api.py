"""
This module describes which functions are intended to be used by users to
create papis scripts.
"""
from typing import Any, Dict, List, Optional
import logging

import papis.utils
import papis.commands
import papis.config
import papis.pick
import papis.database

logger = logging.getLogger("api")


def get_lib_name() -> str:
    """
    Get current library, it either retrieves the library from
    the environment PAPIS_LIB variable or from the command line
    args passed by the user.

    :returns: Library name

    >>> get_lib_name() is not None
    True
    """
    return papis.config.get_lib_name()


def set_lib_from_name(library: str) -> None:
    """
    Set current library, it either sets the library in
    the environment PAPIS_LIB variable or in the command line
    args passed by the user.

    :param library: Name of library or path to a given library
    """
    papis.config.set_lib_from_name(library)


def get_libraries() -> List[str]:
    """
    Get all libraries declared in the configuration. A library is discovered
    if the ``dir`` or ``dirs`` key defined in the library section.

    :returns: List of library names

    >>> len(get_libraries()) >= 1
    True
    """
    libs = []
    config = papis.config.get_configuration()
    for key in config:
        if "dir" in config[key] or "dirs" in config[key]:
            libs.append(key)
    return libs


pick_doc = papis.pick.pick_doc
pick = papis.pick.pick


def open_file(file_path: str, wait: bool = True) -> None:
    """
    Open file using the ``opentool`` key value as a program to
    handle file_path.

    :param file_path: File path to be handled.
    :param wait: Wait for the completion of the opener program to continue
    """
    papis.utils.open_file(file_path, wait=wait)


def open_dir(dir_path: str, wait: bool = True) -> None:
    """
    Open dir using the ``file-browser`` key value as a program to
    open dir_path.

    :param dir_path: Folder path to be handled.
    :param wait: Wait for the completion of the opener program to continue
    """
    papis.utils.general_open(dir_path, "file-browser", wait=wait)


def edit_file(file_path: str, wait: bool = True) -> None:
    """
    Edit file using the ``editor`` key value as a program to
    handle file_path.

    :param file_path: File path to be handled.
    :param wait: Wait for the completion of the opener program to continue
    """
    papis.utils.general_open(file_path, "editor", wait=wait)


def get_all_documents_in_lib(
        library: Optional[str] = None) -> List[papis.document.Document]:
    """
    Get ALL documents contained in the given library with possibly.

    :param library: Library name.
    :returns: List of all documents.

    >>> import tempfile
    >>> folder = tempfile.mkdtemp()
    >>> set_lib_from_name(folder)
    >>> docs = get_all_documents_in_lib(folder)
    >>> len(docs)
    0
    """
    return papis.database.get(library).get_all_documents()


def get_documents_in_dir(
        directory: str, search: str = "") -> List[papis.document.Document]:
    """
    Get documents contained in the given folder with possibly a search
    string.

    :param directory: Folder path.
    :param search: Search string
    :returns: List of filtered documents.

    >>> import tempfile
    >>> docs = get_documents_in_dir(tempfile.mkdtemp())
    >>> len(docs)
    0

    """
    set_lib_from_name(directory)
    return get_documents_in_lib(directory, search)


def get_documents_in_lib(
        library: Optional[str] = None,
        search: str = "") -> List[papis.document.Document]:
    """
    Get documents contained in the given library with possibly a search
    string.

    :param library: Library name.
    :param search: Search string
    :returns: List of filtered documents.
    """
    return papis.database.get(library).query(search)


def clear_lib_cache(lib: Optional[str] = None) -> None:
    """
    Clear cache associated with a library. If no library is given
    then the current library is used.

    :param lib: Library name.

    >>> clear_lib_cache()
    """
    papis.database.get(lib).clear()


def doi_to_data(doi: str) -> Dict[str, Any]:
    """
    Try to get from a DOI expression a dictionary with the document's data
    using the crossref module.

    :param doi: DOI expression.
    :returns: Document's data
    """
    import papis.crossref
    return papis.crossref.doi_to_data(doi)
