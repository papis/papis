from ..document import Document
import papis
import sys
import os
import papis.utils
from . import Command


class Export(Command):
    def init(self):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """
        # export parser
        export_parser = self.parser.add_parser("export",
                help="Export a document from a given library")
        export_parser.add_argument(
                "document",
                help="Document search",
                nargs="?",
                default=".",
                action="store")
        export_parser.add_argument(
            "--bibtex",
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
        documentsDir = os.path.expanduser(config[args.lib]["dir"])
        self.logger.debug("Using directory %s"%documentsDir)
        documentSearch = args.document
        folders = papis.utils.getFilteredFolders(documentsDir, documentSearch)
        for folder in folders:
            self.logger.debug(folder)
            document = Document(folder)
            if args.bibtex:
                print(document.toBibtex())
            else:
                print(document.dump())
