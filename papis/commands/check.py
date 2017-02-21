from ..document import Paper
import papis
from . import Command


class Check(Command):
    def init(self, parser):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """
        check_parser = parser.add_parser("check",
                help="Check paper document from a given library")
        check_parser.add_argument("paper",
                help="Paper search",
                nargs="?",
                default=".",
                action="store")

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
        folders = papis.getFolders(papersDir)
        folders = papis.filterPaper(folders, paperSearch)
        allOk = True
        for folder in folders:
            printv(folder)
            paper   = Paper(folder)
            allOk &= paper.check()
        if not allOk:
            print("Errors were detected, please fix the info files")
        else:
            print("No errors detected")
