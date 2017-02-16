from ..document import Paper


def init(subparsers):
    """TODO: Docstring for init.

    :subparser: TODO
    :returns: TODO

    """
    # update parser
    update_parser = subparsers.add_parser("update",
            help="Update a paper from a given library")
    update_parser.add_argument("--from-bibtex",
        help    = "Update info from bibtex file",
        action  = "store"
    )
    update_parser.add_argument("-i",
        "--interactive",
        help    = "Interactively update",
        default = False,
        action  = "store_true"
    )
    update_parser.add_argument("-f",
        "--force",
        help    = "Force update, overwrite conflicting information",
        default = False,
        action  = "store_true"
    )
    update_parser.add_argument("paper",
            help="Paper search",
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
    data  = bibTexToDict(args.from_bibtex) \
            if args.from_bibtex else dict()
    folders = getFolders(papersDir)
    folders = filterPaper(folders, paperSearch)
    folder  = folders[0]
    paper   = Paper(folder)
    paper.update(data, args.force, args.interactive)
    paper.save()

