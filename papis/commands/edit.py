import papis
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
        self.subparser = self.parser.add_parser(
            "edit",
            help="Edit document information from a given library"
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
        documents = papis.utils.getFilteredDocuments(
            documentsDir,
            documentSearch
        )
        document = self.pick(documents, config)
        if args.notes:
            if not document.has("notes"):
                self.logger.warning(
                    "The document selected has no notes attached,\
                    creating one..."
                )
                document["notes"] = "notes.tex"
                document.save()
            notesName = document["notes"]
            notesPath = os.path.join(
                document.getMainFolder(),
                notesName
            )
            if not os.path.exists(notesPath):
                self.logger.debug("Creating %s" % notesPath)
                open(notesPath, "w+").close()
            papis.utils.editFile(notesPath, config)
        else:
            papis.utils.editFile(document.getInfoFile(), config)
