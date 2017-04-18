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
            "--tool",
            help="Tool for opening the file (opentool)",
            default="",
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
        if args.tool:
            config["settings"]["opentool"] = args.tool
        self.logger.debug("Using directory %s" % documentsDir)
        documentSearch = args.document
        documents = papis.utils.getFilteredDocuments(
            documentsDir,
            documentSearch
        )
        document = self.pick(documents, config)
        files = document.getFiles()
        file_to_open = papis.utils.pick(
            files,
            config,
            pick_config=dict(
                header_filter=lambda x: x.replace(document.getMainFolder(), "")
            )
        )
        papis.utils.openFile(file_to_open, config)
