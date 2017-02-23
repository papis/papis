from subprocess import call
from subprocess import Popen, PIPE
import glob
import logging
import os
import sys
import re
import papis.pick

logger = logging.getLogger("utils")

def which(program):
    # source http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
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

def pick(files, configuration = {}):
    """TODO: Docstring for editFile.
    :fileName: TODO
    :returns: TODO
    """
    try:
        logger.debug("Parsing picktool")
        picker = configuration["settings"]["picktool"]
    except KeyError:
        return papis.pick.pick(files)
    else:
        # FIXME: Do it more fancy
        return Popen(
                "echo "+"\n".join(files)+" | "+picker,
                stdout=PIPE,
                shell=True).read()

def openFile(fileName, configuration = {}):
    """TODO: Docstring for openFile.
    :fileName: TODO
    :returns: TODO
    """
    try:
        opener = configuration["settings"]["viewer"]
    except KeyError:
        opener = "xdg-open"
    call([opener, fileName])

def editFile(fileName, configuration = {}):
    """TODO: Docstring for editFile.
    :fileName: TODO
    :returns: TODO
    """
    try:
        editor = configuration["settings"]["editor"]
    except KeyError:
        editor = os.environ["EDITOR"]
    call([editor, fileName])

def filterDocument(folders, documentInput):
    """

    :folders: TODO
    :documentInput: TODO
    :returns: TODO

    """
    results = []
    regex   = r".*"+re.sub(r"([0-9a-zA-Z])", "\\1.*", documentInput.strip().replace(" ",""))
    logger.debug("Filter regex = %s"%regex)
    for folder in folders:
        if re.match(regex, folder, re.IGNORECASE):
            results.append(folder)
    if len(results) == 0:
        print("No results found with the given input")
        sys.exit(1)
    return results

def getFilteredFolders(directory, search):
    """
    Get documents from a containing folder
    :folder: TODO
    :returns: TODO
    """
    folders = getFolders(directory)
    folders = filterDocument(folders, search)
    return folders

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
