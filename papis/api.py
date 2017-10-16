"""This module describes which functions are intended to be used by users to
create papis scripts.
"""

from subprocess import call
import logging

logger = logging.getLogger("api")
logger.debug("importing")

import os
import re
import papis.cache
import papis.utils
import papis.commands
import papis.config


def get_lib():
    """Get current library, it either retrieves the library from
    the environment PAPIS_LIB variable or from the command line
    args passed by the user.

    :returns: Library name
    :rtype:  str

    >>> get_lib() == papis.config.get_default_settings(key='default-library')
    True
    >>> set_lib('books')
    >>> get_lib()
    'books'
    """
    return papis.config.get_lib()


def set_lib(library):
    """Set current library, it either sets the library in
    the environment PAPIS_LIB variable or in the command line
    args passed by the user.

    :param library: Name of library or path to a given library
    :type  library: str

    """
    try:
        args = papis.commands.get_args()
        args.lib = library
    except AttributeError:
        os.environ["PAPIS_LIB"] = library


def get_arg(arg, default=None):
    try:
        val = getattr(papis.commands.get_args(), arg)
    except AttributeError:
        try:
            val = os.environ["PAPIS_"+arg.upper()]
        except KeyError:
            val = default
    return val


def get_libraries():
    """Get all libraries declared in the configuration. A library is discovered
    if the ``dir`` key defined in the library section.

    :returns: List of library names
    :rtype: list

    """
    libs = []
    config = papis.config.get_configuration()
    for key in config.keys():
        if "dir" in config[key]:
            libs.append(key)
    return libs


def pick_doc(documents):
    """Pick a document from documents with the correct formatting

    :documents: List of documents
    :returns: Document

    """
    header_format = papis.config.get("header-format")
    match_format = papis.config.get("match-format")
    pick_config = dict(
        header_filter=lambda x: papis.utils.format_doc(header_format, x),
        match_filter=lambda x: papis.utils.format_doc(match_format, x)
    )
    return papis.api.pick(
        documents,
        pick_config
    )


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

    >>> papis.config.set('picktool', 'papis.pick')
    >>> pick(['something'])
    'something'

    """
    # Leave this import here
    import papis.config
    logger.debug("Parsing picktool")
    picker = papis.config.get("picktool")
    if picker == "rofi":
        import papis.gui.rofi
        logger.debug("Using rofi picker")
        return papis.gui.rofi.pick(options, **pick_config)
    elif picker == "vim":
        import papis.gui.vim
        logger.debug("Using vim picker")
        return papis.gui.vim.pick(options, **pick_config)
    elif picker == "papis.pick":
        import papis.pick
        logger.debug("Using papis.pick picker")
        return papis.pick.pick(options, **pick_config)
    else:
        raise Exception("I don't know how to use the picker '%s'" % picker)


def open_file(file_path):
    """Open file using the ``opentool`` key value as a program to
    handle file_path.

    :param file_path: File path to be handled.
    :type  file_path: str

    """
    papis.utils.general_open(file_path, "opentool")


def open_dir(dir_path):
    """Open dir using the ``file-browser`` key value as a program to
    open dir_path.

    :param dir_path: Folder path to be handled.
    :type  dir_path: str

    """
    papis.utils.general_open(dir_path, "file-browser")


def edit_file(file_path):
    """Edit file using the ``editor`` key value as a program to
    handle file_path.

    :param file_path: File path to be handled.
    :type  file_path: str

    """
    papis.utils.general_open(file_path, "editor")


def get_documents_in_dir(directory, search=""):
    """Get documents contained in the given folder with possibly a search
    string.

    :param directory: Folder path.
    :type  directory: str

    :param search: Search string
    :type  search: str

    :returns: List of filtered documents.
    :rtype: list

    >>> docs = get_documents_in_dir('non/existent/path')
    >>> len(docs)
    0

    """
    return papis.utils.get_documents(directory, search)


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
    directory = library if os.path.exists(library) \
        else papis.config.get("dir", section=library)
    return papis.api.get_documents_in_dir(directory, search)


def clear_lib_cache(lib=None):
    """Clear cache associated with a library. If no library is given
    then the current library is used.

    :param lib: Library name.
    :type  lib: str

    """
    lib = papis.api.get_lib() if lib is None else lib
    directory = papis.config.get("dir", section=lib)
    papis.cache.clear(directory)
