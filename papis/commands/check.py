from ..document import Document
import papis
import sys
import os
import papis.utils
from . import Command


class Check(Command):
    def init(self, parser):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """
        check_parser = parser.add_parser("check",
                help="Check document document from a given library")
        check_parser.add_argument("document",
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
        documentSearch = args.paper
        folders = papis.utils.getFolders(documentsDir)
        folders = papis.utils.filterDocument(folders, documentSearch)
        allOk = True
        for folder in folders:
            self.logger.debug(folder)
            document   = Document(folder)
            allOk &= document.check()
        if not allOk:
            print("Errors were detected, please fix the info files")
        else:
            print("No errors detected")
