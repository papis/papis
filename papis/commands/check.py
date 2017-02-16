from ..document import Paper


def init(subparsers):
    """TODO: Docstring for init.

    :subparser: TODO
    :returns: TODO

    """
    check_parser = subparsers.add_parser("check",
            help="Check paper document from a given library")
    check_parser.add_argument("paper",
            help="Paper search",
            nargs="?",
            default=".",
            action="store")

def main(config, args):
    """
    Main action if the command is triggered

    :config: User configuration
    :args: CLI user arguments
    :returns: TODO

    """
    papersDir = os.path.expanduser(config[args.lib]["dir"])
    printv("Using directory %s"%papersDir)
    paperSearch = args.paper
    folders = getFolders(papersDir)
    folders = filterPaper(folders, paperSearch)
    allOk = True
    for folder in folders:
        printv(folder)
        paper   = Paper(folder)
        allOk &= paper.check()
    if not allOk:
        print("Errors were detected, please fix the info files")
    else:
        print("No errors detected")
