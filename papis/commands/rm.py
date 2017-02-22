import webbrowser
from ..document import Document
import papis
import sys
import os
import shutil
import papis.utils
from . import Command

class Rm(Command):
    def init(self):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """

        parser = self.parser.add_parser("rm",
                help="Delete entry"
                )
        parser.add_argument("document",
                help="Document search",
                nargs="?",
                default=".",
                action="store"
                )
        parser.add_argument("-f", "--force",
                help="Do not confirm removal",
                default=False,
                action="store_true"
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
        folder = papis.utils.pick(folders, config)
        document = Document(folder)
        if not args.force:
            if input("Are you sure? (Y/n): ") in ["N","n"]:
                sys.exit(0)
        print("Removing %s..."%folder)
        shutil.rmtree(folder)
