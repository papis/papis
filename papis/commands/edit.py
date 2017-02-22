from ..document import Document
import papis
import sys
import os
import papis.utils
from . import Command



class Edit(Command):
    def init(self, parser):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """
        edit_parser = parser.add_parser("edit",
                help="Edit document information from a given library")
        edit_parser.add_argument("document",
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
        document   = Document(folders[0])
        papis.utils.editFile(document.getInfoFile(), config)
