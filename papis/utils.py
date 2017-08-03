from subprocess import call
import logging

logger = logging.getLogger("utils")
logger.debug("importing")

import os
import re
import papis.pick
import papis.config
import papis.commands
import papis.document
import papis.crossref
import papis.bibtex



def get_lib():
    """Get current library, it either retrieves the library from
    the environment PAPIS_LIB variable or from the command line
    args passed by the user.

    :param library: Name of library or path to a given library
    :type  library: str
    """
    try:
        lib = papis.commands.get_args().lib
    except AttributeError:
        try:
            lib = os.environ["PAPIS_LIB"]
        except KeyError:
            # Do not put papis.config.get because get is a special function
            # that also needs the library to see if some key was overriden!
            lib = papis.config.get_default_settings(key="default-library")
    return lib


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


def pick(options, pick_config={}):
    """This is a wrapper for the various pickers that are supported.
    Depending on the configuration different selectors or 'pickers'
    are used.
    :param options: List of different objects. The type of the objects within
        the list must be supported by the pickers. This is the reason why this
        function is difficult to generalize for external picker programs.
    :type  options: list
    :param pick_config: Dictionary with additional configuration for the
        used picker. This depends on the picker.
    :type  pick_config: dict
    :returns: Returns elements of ``options``.
    :rtype: Element(s) of ``options``
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
        logger.debug("Using papis.pick picker")
        return papis.pick.pick(options, **pick_config)
    else:
        raise Exception("I don't know how to use the picker '%s'" % picker)


def general_open(fileName, key, default_opener="xdg-open", wait=False):
    try:
        opener = papis.config.get(key)
    except KeyError:
        opener = default_opener
    if isinstance(fileName, list):
        fileName = pick(fileName)
    if isinstance(opener, str):
        if wait:
            return os.system(" ".join([opener, fileName]))
        else:
            return call([opener, fileName])
    elif hasattr(opener, '__call__'):
        return opener(fileName)
    else:
        raise Warning("How should I use the opener %s?" % opener)


def open_file(file_path):
    """Open file using the ``opentool`` key value as a program to
    handle file_path.

    :param file_path: File path to be handled.
    :type  file_path: str
    """
    general_open(file_path, "opentool")


def open_dir(dir_path):
    """Open dir using the ``file-browser`` key value as a program to
    open dir_path.

    :param dir_path: Folder path to be handled.
    :type  dir_path: str
    """
    general_open(dir_path, "file-browser")


def edit_file(file_path):
    """Edit file using the ``editor`` key value as a program to
    handle file_path.

    :param file_path: File path to be handled.
    :type  file_path: str
    """
    general_open(file_path, "editor")


def get_regex_from_search(search):
    """Creates a default regex from a search string.

    :param search: A valid search string
    :type  search: str
    :returns: Regular expression
    :rtype: str
    """
    return r".*"+re.sub(r"\s+", ".*", search)

def format_doc(python_format, document):
    """Construct a string using a pythonic format string and a document.

    :param python_format: Python-like format string.
        (`see <
            https://docs.python.org/2/library/string.html#format-string-syntax
        >`_)
    :type  python_format: str
    :param document: Papis document
    :type  document: papis.document.Document
    :returns: Formated string
    :rtype: str
    """
    doc = papis.config.get("format-doc-name")
    return python_format.format(**{doc: document})


def match_document(document, search, match_format=None):
    """Main function to match document to a given search.

    :param document: Papis document
    :type  document: papis.document.Document
    :param search: A valid search string
    :type  search: str
    :param match_format: Python-like format string.
        (`see <
            https://docs.python.org/2/library/string.html#format-string-syntax
        >`_)
    :type  match_format: str
    :returns: Non false if matches, true-ish if it does match.
    """
    match_format = match_format or papis.config.get("match-format")
    match_string = format_doc(match_format, document)
    regex = get_regex_from_search(search)
    return re.match(regex, match_string, re.IGNORECASE)


def get_documents_in_dir(directory, search=""):
    """Get documents contained in the given folder with possibly a search
    string.

    :param directory: Folder path.
    :type  directory: str
    :param search: Search string
    :type  search: str
    :returns: List of filtered documents.
    :rtype: list
    """
    return get_documents(directory, search)


def get_documents_in_lib(library, search=""):
    """Get documents contained in the given library with possibly a search
    string.

    :param library: Library name.
    :type  library: str
    :param search: Search string
    :type  search: str
    :returns: List of filtered documents.
    :rtype: list
    """
    directory = papis.config.get("dir", section=library)
    return get_documents_in_dir(directory, search)


def get_folders(folder):
    """This is the main indexing routine. It looks inside ``folder`` and crawls
    the whole directory structure in search for subfolders containing an info
    file.

    :param folder: Folder to look into.
    :type  folder: str
    :returns: List of folders containing an info file.
    :rtype: list
    """
    logger.debug("Indexing folders")
    folders = list()
    for root, dirnames, filenames in os.walk(folder):
        if os.path.exists(os.path.join(root, get_info_file_name())):
            folders.append(root)
    return folders


class DocMatcher(object):
    search = ""
    @classmethod
    def return_if_match(cls, doc):
        return doc if papis.utils.match_document(doc, cls.search) else None


def filter_documents(documents, search=""):
    """Filter documents. It can be done in a multi core way.

    :param documents: List of papis documents.
    :type  documents: papis.documents.Document
    :param search: Valid papis search string.
    :type  search: str
    :returns: List of filtered documents
    :rtype:  list

    """
    logger = logging.getLogger('filter')
    papis.utils.DocMatcher.search = search
    if search == "" or search == ".":
        return documents
    else:
        # Doing this multiprocessing in filtering does not seem
        # to help much, I don't know if it's because I'm doing something
        # wrong or it is really like this.
        import multiprocessing
        import time
        np = get_arg("cores", multiprocessing.cpu_count())
        pool = multiprocessing.Pool(np)
        logger.debug(
            "Filtering docs (search %s) using %s cores" % (
                search,
                np
            )
        )
        logger.debug("pool started")
        begin_t = time.time()
        result = pool.map(
            papis.utils.DocMatcher.return_if_match, documents
        )
        pool.close()
        pool.join()
        logger.debug("pool done (%s ms)" % (1000*time.time()-1000*begin_t))
        return [d for d in result if d is not None]


def get_documents(directory, search=""):
    """Get documents from within a containing folder

    :param directory: Folder to look for documents.
    :type  directory: str
    :param search: Valid papis search
    :type  search: str
    :returns: List of document objects.
    :rtype: list
    """
    import papis.config
    directory = os.path.expanduser(directory)

    if papis.config.getboolean("use-cache"):
        import papis.cache
        folders = papis.cache.get_folders(directory)
    else:
        folders = get_folders()

    logger.debug("Creating document objects")
    documents = folders_to_documents(folders)
    logger.debug("Done")

    return filter_documents(documents, search)


def folders_to_documents(folders):
    """Turn folders into documents, this is done in a multiprocessing way, this
    step is quite critical for performance.

    :param folders: List of folder paths.
    :type  folders: list
    :returns: List of document objects.
    :rtype:  list
    """
    import multiprocessing
    import time
    logger = logging.getLogger("dir2doc")
    np = get_arg("cores", multiprocessing.cpu_count())
    logger.debug("Running in %s cores" % np)
    pool = multiprocessing.Pool(np)
    logger.debug("pool started")
    begin_t = time.time()
    result = pool.map(papis.document.Document, folders)
    pool.close()
    pool.join()
    logger.debug("pool done (%s ms)" % (1000*time.time()-1000*begin_t))
    return result


def folder_is_git_repo(folder):
    """Check if folder is a git repository

    :folder: Folder to check
    :returns: Wether is git repo or not
    :rtype:  bool

    """
    import subprocess
    logger.debug("Check if %s is a git repo" % folder)
    try:
        subprocess.check_call(
            ' '.join(['git', '-C', folder, 'status']),
            stdout=None,
            shell=True
        )
        logger.debug("Detected git repo in %s" % folder)
        return True
    except:
        return False


def lib_is_git_repo(library):
    """Check if library is a git repository

    :library: Library to check
    :returns: Wether is git repo or not
    :rtype:  bool
    """
    config = papis.config.get_configuration()
    return folder_is_git_repo(config.get(library, "dir"))


def get_info_file_name():
    """Get the name of the general info file for any document

    :returns: Name of the file.
    :rtype: str
    """
    return papis.config.get("info-name")


def clear_lib_cache(lib=None):
    """Clear cache associated with a library. If no library is given
    then the current library is used.

    :param lib: Library name.
    :type  lib: str
    """
    import papis.cache
    lib = papis.utils.get_lib() if lib is None else lib
    directory = papis.config.get("dir", section=lib)
    papis.cache.clear(directory)


def doi_to_data(doi):
    """Try to get from a DOI expression a dictionary with the document's data
    using the crossref module.

    :param doi: DOI expression.
    :type  doi: str
    :returns: Document's data
    :rtype: dict
    """
    return papis.crossref.doi_to_data(doi)


def yaml_to_data(yaml_path):
    """Convert a yaml file into a dictionary using the yaml module.

    :param yaml_path: Path to a yaml file
    :type  yaml_path: str
    :returns: Dictionary containing the info of the yaml file
    :rtype:  dict
    """
    import yaml
    return yaml.load(open(self.args.from_yaml))


def vcf_to_data(vcard_path):
    """Convert a vcf file into a dictionary using the vobject module.

    :param vcf_path: Path to a vcf file
    :type  vcf_path: str
    :returns: Dictionary containing the info of the vcf file
    :rtype:  dict
    """
    import vobject
    import yaml
    import papis.document.Document
    data = yaml.load(papis.document.Document.get_vcf_template())
    logger.debug("Reading in %s " % vcard_path)
    text = open(vcard_path).read()
    vcard = vobject.readOne(text)
    try:
        data["first_name"] = vcard.n.value.given
        logger.debug("First name = %s" % data["first_name"])
    except:
        data["first_name"] = None
    try:
        data["last_name"] = vcard.n.value.family
        logger.debug("Last name = %s" % data["last_name"])
    except:
        data["last_name"] = None
    try:
        if not isinstance(vcard.org.value[0], list):
            data["org"] = vcard.org.value
        else:
            data["org"] = vcard.org.value
        logger.debug("Org = %s" % data["org"])
    except:
        data["org"] = []
    for ctype in ["tel", "email"]:
        try:
            vcard_asset = getattr(vcard, ctype)
            logger.debug("Parsing %s" % ctype)
        except:
            pass
        else:
            try:
                param_type = getattr(vcard_asset, "type_param")
            except:
                param_type = "home"
            data[ctype][param_type.lower()] = getattr(vcard_asset, "value")
    logger.debug("Read in data = %s" % data)
    return data


def confirm(prompt, yes=True):
    """Confirm with user input

    :param prompt: Question or text that the user gets.
    :type  prompt: str
    :param yes: If yes should be the default.
    :type  yes: bool
    :returns: True if go ahead, False if stop
    :rtype:  bool

    """
    import prompt_toolkit
    result = prompt_toolkit.prompt(
        prompt + ' (%s): ' % ('Y/n' if yes else 'y/N')
    )
    if yes:
        return result not in ['N', 'n']
    else:
        return result not in ['Y', 'y']
