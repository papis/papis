import papis
import os
import sys
import papis.utils
from . import Command


class Open(Command):
    def init(self):

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

        self.subparser.add_argument(
            "--dir",
            help="Open directory",
            action="store_true"
        )

    def main(self, config, args):

        documentsDir = os.path.expanduser(config[args.lib]["dir"])
        if args.tool:
            config["settings"]["opentool"] = args.tool
        self.logger.debug("Using directory %s" % documentsDir)
        documentSearch = args.document
        documents = papis.utils.getFilteredDocuments(
            documentsDir,
            documentSearch
        )
        if not documents:
            print("No documents found with that name.")
            sys.exit(1)
        document = self.pick(documents, config)
        if not document:
            sys.exit(0)
        if not args.dir:
            files = document.getFiles()
            file_to_open = papis.utils.pick(
                files,
                config,
                pick_config=dict(
                    header_filter=lambda x: x.replace(document.getMainFolder(), "")
                )
            )
            papis.utils.openFile(file_to_open, config)
        else:
            papis.utils.openDir(document.getMainFolder(), config)
