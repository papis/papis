from ..document import Paper
import papis
from . import Command


class List(Command):
    def init(self, parser):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """
        list_parser = parser.add_parser("list",
                help="List papers from a given library")
        list_parser.add_argument("paper",
                help="Paper search",
                default="",
                nargs="?",
                action="store"
                )
        list_parser.add_argument("-i",
            "--info",
            help    = "Show the info file name associated with the paper",
            default = False,
            action  = "store_true"
        )
        list_parser.add_argument("-f",
            "--file",
            help    = "Show the file name associated with the paper",
            default = False,
            action  = "store_true"
        )

    def main(self, config, args):
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
        for folder in folders:
            if args.file:
                paper = Paper(folder)
                print(paper.getFile())
            elif args.info:
                paper = Paper(folder)
                print(os.path.join(paper.getMainFolder(), paper.getInfoFile()))
            else:
                print(folder)
