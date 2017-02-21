from ..document import Paper
import papis
import sys
import os
import papis.util
from . import Command

class Open(Command):
    def init(self, parser):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """

        # open parser
        open_parser = parser.add_parser("open",
                help="Open paper document from a given library")
        open_parser.add_argument("paper",
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
        self.logger.debug("Using directory %s"%papersDir)
        paperSearch = args.paper
        folders = utils.getFolders(papersDir)
        folders = utils.filterPaper(folders, paperSearch)
        paper   = Paper(folders[0])
        utils.openFile(paper.getFile(), config)
