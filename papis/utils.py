from subprocess import call
import logging
import os
import re
import papis.pick
import papis.rofi
import papis.config
import papis.commands
import papis.document
import papis.crossref
import papis.bibtex
# import zipfile
# from lxml import etree

logger = logging.getLogger("utils")


def get_lib():
    try:
        lib = papis.commands.get_args().lib
    except AttributeError:
        lib = os.environ["PAPIS_LIB"]
    return lib


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
        folders = get_cache(cache_path)
    else:
        folders = get_folders(directory)
        create_cache(folders, cache_path)
    logger.debug("Creating document objects")
    # TODO: Optimize this step, do it faster
    # documents = [papis.document.Document(d) for d in folders]
    documents = folders_to_documents(folders)
    logger.debug("Done")
    if search == "" or search == ".":
        return documents
    else:
        logger.debug("Filtering documents with %s " % search)
        documents = [d for d in documents if match_document(d, search)]
        logger.debug("Done")
        return documents


def folders_to_documents(folders):
    """Turn folders into document efficiently
    """
    import multiprocessing
    np = get_arg("cores", os.cpu_count())
    logger.debug("Running in %s cores" % np)
    pool = multiprocessing.Pool(np)
    logger.debug("pool started")
    result = pool.map(papis.document.Document, folders)
    pool.close()
    pool.join()
    logger.debug("pool finished")
    return result


def get_cache(path):
    import pickle
    """Save obj in path
    :obj: Any serializable object
    :path: Path in string
    """
    logger.debug("Getting cache %s " % path)
    return pickle.load(open(path, "rb"))


def create_cache(obj, path):
    import pickle
    """Save obj in path
    :obj: Any serializable object
    :path: Path in string
    """
    logger.debug("Saving in cache %s " % path)
    pickle.dump(obj, open(path, "wb+"))


def get_cache_name(directory):
    import hashlib
    """Get the associated cache name from a directory
    """
    return hashlib\
           .md5(directory.encode())\
           .hexdigest()+"-"+os.path.basename(directory)


def clear_cache(directory):
    """Clear cache associated with a directory
    """
    directory = os.path.expanduser(directory)
    cache_name = get_cache_name(directory)
    cache_path = os.path.join(papis.config.get_cache_folder(), cache_name)
    if os.path.exists(cache_path):
        logger.debug("Clearing cache %s " % cache_path)
        os.remove(cache_path)


def clear_lib_cache(lib):
    """Clear cache associated with a library
    """
    config = papis.config.get_configuration()
    directory = config[lib]["dir"]
    clear_cache(directory)


def folder_is_git_repo(folder):
    """Check if folder is a git repository

    :folder: Folder to check
    :returns: True/False

    """
    logger.debug("Check if %s is a git repo" % folder)
    git_path = os.path.join(os.path.expanduser(folder),".git")
    if os.path.exists(git_path):
        logger.debug("Detected git repo in %s" % git_path)
        return True
    else:
        return False


def lib_is_git_repo(library):
    """Check if library is a git repository

    :folder: Library to check
    :returns: True/False

    """
    config = papis.config.get_configuration()
    return folder_is_git_repo(config.get(library, "dir"))


def get_info_file_name():
    """Get the name of the general info file for any document
    :returns: string

    """
    return "info.yaml"

def doi_to_data(doi):
    bibtex = papis.crossref.doi_to_bibtex(doi)
    return papis.bibtex.bibtex_to_dict(bibtex)


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
