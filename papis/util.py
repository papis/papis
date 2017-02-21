import logging

logger = logging.getLogger("utils")

def which(program):
    # source http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
    import os
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

def pickFile(files, configuration = {}):
    """TODO: Docstring for editFile.
    :fileName: TODO
    :returns: TODO
    """
    from subprocess import Popen, PIPE
    try:
        picker = configuration["settings"]["picker"]
    except KeyError:
        picker = os.environ["PICKER"]
    if not picker:
        return files[0]
    else:
        # FIXME: Do it more fancy
        return Popen("echo "+"\n".join(files)+" | "+picker, stdout=PIPE, shell=True).read()

def openFile(fileName, configuration = {}):
    """TODO: Docstring for openFile.
    :fileName: TODO
    :returns: TODO
    """
    from subprocess import call
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
    from subprocess import call
    try:
        editor = configuration["settings"]["editor"]
    except KeyError:
        editor = os.environ["EDITOR"]
    call([editor, fileName])

def filterPaper(folders, paperInput):
    """

    :folders: TODO
    :paperInput: TODO
    :returns: TODO

    """
    results = []
    regex   = r".*"+re.sub(r"([0-9a-zA-Z])", "\\1.*", paperInput.strip().replace(" ",""))
    logger.debug("Filter regex = %s"%regex)
    for folder in folders:
        if re.match(regex, folder, re.IGNORECASE):
            results.append(folder)
    if len(results) == 0:
        print("No results found with the given input")
        sys.exit(1)
    return results
