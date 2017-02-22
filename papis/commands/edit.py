from ..document import Document
import papis
import sys
import os
import papis.utils
import papis.pick
from . import Command



class Edit(Command):
    def init(self):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """
        edit_parser = self.parser.add_parser(
                "edit",
                help="Edit document information from a given library"
                )
        edit_parser.add_argument(
                "document",
                help="Document search",
                nargs="?",
                default=".",
                action="store"
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
        if len(folders) != 1:
            folder = papis.pick.pick(folders)
        else:
            folder = folders[0]
        if not folder:
            sys.exit(0)
        document   = Document(folder)
        papis.utils.editFile(document.getInfoFile(), config)
