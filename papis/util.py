def header(msg):    print("\n\033[1m"+str(msg)+"\033[0m")
def success(msg):   print(" \033[1;32m==>\033[0m  "+str(msg))
def error(msg):     print(" \033[1;31mX\033[0m  "+str(msg))
def arrow(msg):     print(" \033[1;34m==>\033[0m  "+str(msg))
def warning(msg):   print(" \033[0;93m==>\033[0m  "+str(msg))

def printv(arg1):
    if VERBOSE:
        print(arg1)

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
    printv("Filter regex = %s"%regex)
    for folder in folders:
        if re.match(regex, folder, re.IGNORECASE):
            results.append(folder)
    if len(results) == 0:
        print("No results found with the given input")
        sys.exit(1)
    return results
