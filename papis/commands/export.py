from ..document import Paper
import papis
import sys
import os
import papis.util
from . import Command


class Export(Command):
    def init(self, parser):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """
        # export parser
        export_parser = parser.add_parser("export",
                help="Export a paper from a given library")
        export_parser.add_argument("paper",
                help="Paper search",
                nargs="?",
                default=".",
                action="store")
        export_parser.add_argument("--bibtex",
            help    = "Export into bibtex",
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
        self.logger.debug("Using directory %s"%papersDir)
        paperSearch = args.paper
        folders = papis.utils.getFolders(papersDir)
        folders = papis.utils.filterPaper(folders, paperSearch)
        for folder in folders:
            self.logger.debug(folder)
            paper = Paper(folder)
            if args.bibtex:
                print(paper.toBibtex())
            else:
                print(paper.dump())
