from subprocess import call
from subprocess import Popen, PIPE
import logging
import os
import re
import papis.pick
import papis.config
from .document import Document
# import zipfile
# from lxml import etree

logger = logging.getLogger("utils")
PAPIS_ARGS = None


def set_args(args):
    logger.debug("Setting args")
    global PAPIS_ARGS
    if PAPIS_ARGS is None:
        PAPIS_ARGS = args


def get_args():
    logger.debug("Getting args")
    return PAPIS_ARGS


def get_lib():
    logger.debug("Getting lib")
    return get_args().lib


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
        return papis.pick.pick(options, **pick_config)
    else:
        # FIXME: Do it more fancy
        return Popen(
                "echo "+"\n".join(options)+" | "+picker,
                stdout=PIPE,
                shell=True).read()


def openGeneral(fileName, configuration, key):
    try:
        opener = configuration["settings"][key]
    except KeyError:
        opener = "xdg-open"
    call([opener, fileName])


def open_file(fileName, configuration={}):
    openGeneral(fileName, configuration, "opentool")


def openDir(fileName, configuration={}):
    openGeneral(fileName, configuration, "file-browser")


def edit_file(fileName, configuration={}):
    try:
        editor = configuration["settings"]["editor"]
    except KeyError:
        editor = os.environ["EDITOR"]
    call([editor, fileName])


def matchDocument(document, search):
    match_string = papis.config.get_match_format().format(doc=document)
    regex = r".*"+re.sub(r"\s+", ".*", search)
    m = re.match(regex, match_string, re.IGNORECASE)
    return True if m else False


def get_documents_in_dir(directory, search=""):
    directory = os.path.expanduser(directory)
    documents = [Document(d) for d in getFolders(directory)]
    return [d for d in documents if matchDocument(d, search)]


def get_documents_in_lib(library, search=""):
    config = papis.config.get_configuration()
    directory = config[library]["dir"]
    return get_documents_in_dir(directory, search)


def getFolders(folder):
    """Get documents from a containing folder
    """
    folders = list()
    for root, dirnames, filenames in os.walk(folder):
        if os.path.exists(os.path.join(root, getInfoFileName())):
            folders.append(root)
    return folders


def isGitRepo(folder):
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


def getInfoFileName():
    """TODO: Docstring for getInfoFileName.
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
