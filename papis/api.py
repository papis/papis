"""This module describes which functions are intended to be used by users to
create papis scripts.
"""

import logging
import os
import papis.utils
import papis.commands
import papis.config
import papis.pick
import papis.database

logger = logging.getLogger("api")
logger.debug("importing")


def get_lib_name():
    """Get current library, it either retrieves the library from
    the environment PAPIS_LIB variable or from the command line
    args passed by the user.

    :returns: Library name
    :rtype:  str

    >>> get_lib_name() is not None
    True
    """
    return papis.config.get_lib_name()


def set_lib_from_name(library):
    """Set current library, it either sets the library in
    the environment PAPIS_LIB variable or in the command line
    args passed by the user.

    :param library: Name of library or path to a given library
    :type  library: str

    """
    return papis.config.set_lib_from_name(library)


def get_libraries():
    """Get all libraries declared in the configuration. A library is discovered
    if the ``dir`` or ``dirs`` key defined in the library section.

    :returns: List of library names
    :rtype: list

    >>> len(get_libraries()) >= 1
    True

    """
    libs = []
    config = papis.config.get_configuration()
    for key in config.keys():
        if "dir" in config[key] or "dirs" in config[key]:
            libs.append(key)
    return libs


def pick_doc(documents):
    """Pick a document from documents with the correct formatting

    :documents: List of documents
    :returns: Document

    """
    return papis.pick.pick_doc(documents)


def pick(options, pick_config={}):
    """This is a wrapper for the various pickers that are supported.
    Depending on the configuration different selectors or 'pickers'
    are used.

    :param options: List of different objects. The type of the objects within
        the list must be supported by the pickers. This is the reason why this
        function is difficult to generalize for external picker programs.
    :type  options: list

    :param pick_config: Dictionary with additional configuration for the used
        picker. This depends on the picker.
    :type  pick_config: dict

    :returns: Returns elements of ``options``.
    :rtype: Element(s) of ``options``

    """
    return papis.pick.pick(options, **pick_config)


def open_file(file_path, wait=True):
    """Open file using the ``opentool`` key value as a program to
    handle file_path.

    :param file_path: File path to be handled.
    :type  file_path: str
    :param wait: Wait for the completion of the opener program to continue
    :type  wait: bool

    """
    papis.utils.general_open(file_path, "opentool", wait=wait)


def open_dir(dir_path, wait=True):
    """Open dir using the ``file-browser`` key value as a program to
    open dir_path.

    :param dir_path: Folder path to be handled.
    :type  dir_path: str
    :param wait: Wait for the completion of the opener program to continue
    :type  wait: bool

    """
    papis.utils.general_open(dir_path, "file-browser", wait=wait)


def edit_file(file_path, wait=True):
    """Edit file using the ``editor`` key value as a program to
    handle file_path.

    :param file_path: File path to be handled.
    :type  file_path: str
    :param wait: Wait for the completion of the opener program to continue
    :type  wait: bool

    """
    papis.utils.general_open(file_path, "editor", wait=wait)


def get_all_documents_in_lib(library=None):
    """Get ALL documents contained in the given library with possibly.

    :param library: Library name.
    :type  library: str

    :returns: List of all documents.
    :rtype: list

    >>> import tempfile
    >>> folder = tempfile.mkdtemp()
    >>> set_lib_from_name(folder)
    >>> docs = get_all_documents_in_lib(folder)
    >>> len(docs)
    0

    """
    return papis.database.get(library=library).get_all_documents()


def get_documents_in_dir(directory, search=""):
    """Get documents contained in the given folder with possibly a search
    string.

    :param directory: Folder path.
    :type  directory: str

    :param search: Search string
    :type  search: str

    :returns: List of filtered documents.
    :rtype: list

    >>> import tempfile
    >>> docs = get_documents_in_dir(tempfile.mkdtemp())
    >>> len(docs)
    0

    """
    set_lib_from_name(directory)
    return get_documents_in_lib(directory, search)


def get_documents_in_lib(library=None, search=""):
    """Get documents contained in the given library with possibly a search
    string.

    :param library: Library name.
    :type  library: str

    :param search: Search string
    :type  search: str

    :returns: List of filtered documents.
    :rtype: list

    """
    return papis.database.get(library=library).query(search)


def clear_lib_cache(lib=None):
    """Clear cache associated with a library. If no library is given
    then the current library is used.

    :param lib: Library name.
    :type  lib: str

    >>> clear_lib_cache()

    """
    papis.database.get(lib).clear()


def doi_to_data(doi):
    """Try to get from a DOI expression a dictionary with the document's data
    using the crossref module.

    :param doi: DOI expression.
    :type  doi: str
    :returns: Document's data
    :rtype: dict
    """
    return papis.crossref.doi_to_data(doi)
