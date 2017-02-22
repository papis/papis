from ..document import Document
import papis
import sys
import os
import papis.utils
from . import Command

class Open(Command):
    def init(self):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """

        # open parser
        open_parser = self.parser.add_parser("open",
                help="Open document document from a given library")
        open_parser.add_argument("document",
                help="Document search",
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
        documentsDir = os.path.expanduser(config[args.lib]["dir"])
        self.logger.debug("Using directory %s"%documentsDir)
        documentSearch = args.document
        folders = papis.utils.getFilteredFolders(documentsDir, documentSearch)
        folder = papis.utils.pick(folders, config)
        document   = Document(folder)
        papis.utils.openFile(document.getFile(), config)
