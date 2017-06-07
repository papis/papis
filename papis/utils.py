from subprocess import call
from subprocess import Popen, PIPE
import logging
import os
import re
import papis.pick
import papis.rofi
import papis.config
import papis.commands
from .document import Document
# import zipfile
# from lxml import etree

logger = logging.getLogger("utils")


def get_lib():
    try:
        lib = papis.commands.get_args().lib
    except AttributeError:
        lib = os.environ["PAPIS_LIB"]
    return lib


def get_libraries():
    libs = []
    config = papis.config.get_configuration()
    for key in config.keys():
        if "dir" in config[key]:
            libs.append(key)
    return libs


def which(program):
    # source
    # stackoverflow.com/questions/377017/test-if-executable-exists-in-python
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


def pick(options, papis_config={}, pick_config={}):
    try:
        logger.debug("Parsing picktool")
        picker = papis.config.get("picktool")
    except KeyError:
        logger.debug("Using default picker")
        return papis.pick.pick(options, **pick_config)
    else:
        if picker == "rofi":
            logger.debug("Using rofi picker")
            return papis.rofi.pick(options, **pick_config)


def general_open(fileName, key, default_opener="xdg-open", wait=False):
    config = papis.config.get_configuration()
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



def open_file(fileName):
    general_open(fileName, "opentool")


def open_dir(fileName):
    general_open(fileName, "file-browser")


def edit_file(fileName, configuration={}):
    general_open(fileName, "editor", default_opener=os.environ["EDITOR"])


def match_document(document, search, match_format=""):
    if not match_format:
        match_format = papis.config.get_match_format()
    match_string = match_format.format(doc=document)
    regex = r".*"+re.sub(r"\s+", ".*", search)
    m = re.match(regex, match_string, re.IGNORECASE)
    return True if m else False


def get_documents_in_dir(directory, search=""):
    return get_documents(directory, search)


def get_documents_in_lib(library, search=""):
    config = papis.config.get_configuration()
    directory = config[library]["dir"]
    return get_documents_in_dir(directory, search)


def get_folders(folder):
    """Get documents from a containing folder
    """
    logger.debug("Indexing folders")
    folders = list()
    for root, dirnames, filenames in os.walk(folder):
        if os.path.exists(os.path.join(root, get_info_file_name())):
            folders.append(root)
    return folders


def get_documents(directory, search=""):
    """Get documents from within a containing folder
    """
    import pickle
    directory = os.path.expanduser(directory)
    cache = papis.config.get_cache_folder()
    cache_name = get_cache_name(directory)
    cache_path = os.path.join(cache, cache_name)
    folders = []
    logger.debug("Getting documents from dir %s" % directory)
    logger.debug("Cache path = %s" % cache_path)
    if not os.path.exists(cache):
        logger.debug("Creating cache dir %s " % cache)
        os.makedirs(cache)
    if os.path.exists(cache_path):
        logger.debug("Loading folders from cache")
        folders = pickle.load(open(cache_path, "rb"))
    else:
        folders = get_folders(directory)
        logger.debug("Saving folders in cache %s " % cache_path)
        pickle.dump(folders, open(cache_path, "wb+"))
    logger.debug("Creating document objects")
    documents = [Document(d) for d in folders]
    if not search:
        return documents
    else:
        logger.debug("Filtering documents with %s " % search)
        return [d for d in documents if match_document(d, search)]


def get_cache_name(directory):
    import hashlib
    """Get the associated cache name from a directory
    """
    return hashlib.md5(directory.encode()).hexdigest()+"-"+os.path.basename(directory)


def clear_cache(directory):
    """Clear cache associated with a directory
    """
    directory = os.path.expanduser(directory)
    cache_name = get_cache_name(directory)
    cache_path = os.path.join(papis.config.get_cache_folder(), cache_name)
    logger.debug("Clearing cache %s " % cache_path)
    os.remove(cache_path)


def clear_lib_cache(lib):
    """Clear cache associated with a library
    """
    config = papis.config.get_configuration()
    directory = config[lib]["dir"]
    clear_cache(directory)


def is_git_repo(folder):
    """Check if folder is a git repository

    :folder: Folder to check
    :returns: True/False

    """
    logger = logging.getLogger("is_git")
    if os.path.exists(os.path.join(folder, ".git")):
        logger.debug("Detected git repo in %s" % folder)
        return True
    else:
        return False


def get_info_file_name():
    """TODO: Docstring for get_info_file_name.
    :returns: TODO

    """
    return "info.yaml"


def get_epub_info(fname):
    # ns = {
        # 'n': 'urn:oasis:names:tc:opendocument:xmlns:container',
        # 'pkg': 'http://www.idpf.org/2007/opf',
        # 'dc': 'http://purl.org/dc/elements/1.1/'
    # }

    res = {}

    # prepare to read from the .epub file
    # zip = zipfile.ZipFile(fname)

    # # find the contents metafile
    # txt = zip.read('META-INF/container.xml')
    # tree = etree.fromstring(txt)
    # cfname = \
    #   tree.xpath('n:rootfiles/n:rootfile/@full-path', namespaces=ns)[0]

    # # grab the metadata block from the contents metafile
    # cf = zip.read(cfname)
    # tree = etree.fromstring(cf)
    # p = tree.xpath('/pkg:package/pkg:metadata', namespaces=ns)[0]

    # # repackage the data
    # for s in ['title', 'language', 'creator', 'date', 'identifier']:
    #     res[s] = p.xpath('dc:%s/text()' % (s), namespaces=ns)[0]
    return res
