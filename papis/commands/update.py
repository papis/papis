from ..document import Document
import papis
import sys
import os
import papis.utils
import papis.bibtex
from . import Command


class Update(Command):
    def init(self):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """
        # update parser
        update_parser = self.parser.add_parser("update",
                help="Update a document from a given library")
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
        update_parser.add_argument("document",
                help="Document search",
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
        data  = papis.bibtex.bibtexToDict(args.from_bibtex) \
                if args.from_bibtex else dict()
        folders = papis.utils.getFilteredFolders(documentsDir, documentSearch)
        folder  = folders[0]
        document   = Document(folder)
        document.update(data, args.force, args.interactive)
        document.save()

