from ..document import Document
import papis
import sys
import os
import papis.utils
from . import Command


class List(Command):
    def init(self):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """
        list_parser = self.parser.add_parser("list",
                help="List documents from a given library")
        list_parser.add_argument("document",
                help="Document search",
                default="",
                nargs="?",
                action="store"
                )
        list_parser.add_argument("-i",
            "--info",
            help    = "Show the info file name associated with the document",
            default = False,
            action  = "store_true"
        )
        list_parser.add_argument("-f",
            "--file",
            help    = "Show the file name associated with the document",
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
        documentsDir = os.path.expanduser(config[args.lib]["dir"])
        self.logger.debug("Using directory %s"%documentsDir)
        documentSearch = args.document
        folders = papis.utils.getFilteredFolders(documentsDir, documentSearch)
        for folder in folders:
            if args.file:
                document = Document(folder)
                print(document.getFile())
            elif args.info:
                document = Document(folder)
                print(os.path.join(document.getMainFolder(), document.getInfoFile()))
            else:
                print(folder)
