from subprocess import call
from subprocess import Popen, PIPE
import logging
import os
import sys
import re
import papis.pick
from .document import Document

logger = logging.getLogger("utils")


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
    """TODO: Docstring for editFile.
    :fileName: TODO
    :returns: TODO
    """
    try:
        logger.debug("Parsing picktool")
        picker = papis_config["settings"]["picktool"]
    except KeyError:
        return papis.pick.pick(options, **pick_config)
    else:
        # FIXME: Do it more fancy
        return Popen(
                "echo "+"\n".join(options)+" | "+picker,
                stdout=PIPE,
                shell=True).read()


def openFile(fileName, configuration={}):
    """TODO: Docstring for openFile.
    :fileName: TODO
    :returns: TODO
    """
    try:
        opener = configuration["settings"]["viewer"]
    except KeyError:
        opener = "xdg-open"
    call([opener, fileName])


def editFile(fileName, configuration={}):
    """TODO: Docstring for editFile.
    :fileName: TODO
    :returns: TODO
    """
    try:
        editor = configuration["settings"]["editor"]
    except KeyError:
        editor = os.environ["EDITOR"]
    call([editor, fileName])


def matchDocument(document, search):
    match_string = str(document["title"])\
                 + str(document["author"])\
                 + str(document["year"])
    regex = r".*"+re.sub(r"\s+", ".*", search)
    logger.debug("Filter regex = %s" % regex)
    m = re.match(regex, match_string, re.IGNORECASE)
    return True if m else False


def getFilteredDocuments(directory, search):
    documents = [Document(d) for d in getFolders(directory)]
    return [d for d in documents if matchDocument(d, search)]


def getFolders(folder):
    """
    Get documents from a containing folder
    :folder: TODO
    :returns: TODO
    """
    folders = list()
    for root, dirnames, filenames in os.walk(folder):
        if os.path.exists(os.path.join(root, getInfoFileName())):
            folders.append(root)
    return folders


def getInfoFileName():
    """TODO: Docstring for getInfoFileName.
    :returns: TODO

    """
    return "info.yaml"
