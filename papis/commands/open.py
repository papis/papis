from ..document import Document
import papis
import os
import papis.utils
from . import Command


class Open(Command):
    def init(self):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """

        self.subparser = self.parser.add_parser(
            "open",
            help="Open document document from a given library"
        )
        self.subparser.add_argument(
            "document",
            help="Document search",
            nargs="?",
            default=".",
            action="store"
        )
        self.subparser.add_argument(
            "-n",
            "--notes",
            help="Open notes document, if there is some",
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
        self.logger.debug("Using directory %s" % documentsDir)
        documentSearch = args.document
        folders = papis.utils.getFilteredFolders(documentsDir, documentSearch)
        folder = self.pick(folders, config, strip=documentsDir)
        document = Document(folder)
        if args.notes:
            if document.has("notes"):
                notes = os.path.join(
                    document.getMainFolder(),
                    document["notes"]
                )
                papis.utils.openFile(notes, config)
            else:
                self.logger.error(
                        "The document selected has no notes attached"
                        )
        else:
            papis.utils.openFile(document.getFile(), config)
