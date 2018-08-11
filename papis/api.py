"""This module describes which functions are intended to be used by users to
create papis scripts.
"""

import logging

logger = logging.getLogger("api")
logger.debug("importing")

import os
import papis.utils
import papis.commands
import papis.config
import papis.database


class status():
    success = 0
    generic_fail = 1
    file_not_found = 2


def get_lib():
    """Get current library, it either retrieves the library from
    the environment PAPIS_LIB variable or from the command line
    args passed by the user.

    :returns: Library name
    :rtype:  str

    >>> get_lib() is not None
    True
    """
    return papis.config.get_lib()


def set_lib(library):
    """Set current library, it either sets the library in
    the environment PAPIS_LIB variable or in the command line
    args passed by the user.

    :param library: Name of library or path to a given library
    :type  library: str

    """
    return papis.config.set_lib(library)


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

    >>> len(get_libraries()) >= 1
    True

    """
    libs = []
    config = papis.config.get_configuration()
    for key in config.keys():
        if "dir" in config[key]:
            libs.append(key)
    return libs


def pick_doc(documents: list):
    """Pick a document from documents with the correct formatting

    :documents: List of documents
    :returns: Document

    >>> from papis.document import from_data
    >>> doc = from_data({'title': 'Hello World'})
    >>> pick_doc([doc]).dump()
    'title:   Hello World\\n'

    """
    header_format_path = papis.config.get('header-format-file')
    if header_format_path is not None:
        with open(os.path.expanduser(header_format_path)) as fd:
            header_format = fd.read()
    else:
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


def pick(options: list, pick_config={}):
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
    >>> papis.config.set('picktool', 'nonexistent')
    >>> pick(['something'])
    Traceback (most recent call last):
    ...
    Exception: I don\'t know how to use the picker \'nonexistent\'
    >>> papis.config.set('picktool', 'papis.pick')

    """
    # Leave this import here
    import papis.config
    logger.debug("Parsing picktool")
    picker = papis.config.get("picktool")
    if picker == "dmenu":
        import papis.gui.dmenu
        logger.debug("Using dmenu picker")
        return papis.gui.dmenu.pick(options, **pick_config)
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
    >>> set_lib(folder)
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
    set_lib(directory)
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
    lib = papis.api.get_lib() if lib is None else lib
    papis.database.get(lib).clear()
