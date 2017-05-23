import papis
import os
import sys
import papis.utils
from . import Command
import papis.downloaders.utils


class List(Command):
    def init(self):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """
        list_parser = self.parser.add_parser(
            "list",
            help="List documents from a given library"
        )

        list_parser.add_argument(
            "document",
            help="Document search",
            default="",
            nargs="?",
            action="store"
        )

        list_parser.add_argument(
            "-i",
            "--info",
            help="Show the info file name associated with the document",
            default=False,
            action="store_true"
        )

        list_parser.add_argument(
            "-f",
            "--file",
            help="Show the file name associated with the document",
            action="store_true"
        )

        list_parser.add_argument(
            "-d",
            "--dir",
            help="Show the folder name associated with the document",
            default=True,
            action="store_true"
        )

        list_parser.add_argument(
            "-p",
            "--pick",
            help="Pick the document instead of listing everything",
            action="store_true"
        )

        list_parser.add_argument(
            "--downloaders",
            help="List available downloaders",
            action="store_true"
        )

    def main(self, args):
        if args.downloaders:
            for downloader in \
               papis.downloaders.utils.getAvailableDownloaders():
                print(downloader)
            sys.exit(0)
        documentsDir = os.path.expanduser(self.config[args.lib]["dir"])
        self.logger.debug("Using directory %s" % documentsDir)
        documentSearch = args.document
        documents = papis.utils.get_documents_in_dir(
            documentsDir,
            documentSearch
        )
        if args.pick:
            documents = [self.pick(documents)]
        for document in documents:
            if args.file:
                for f in document.get_files():
                    print(f)
            elif args.dir:
                print(document.get_main_folder())
            elif args.info:
                print(
                    os.path.join(
                        document.get_main_folder(),
                        document.getInfoFile()
                    )
                )
            else:
                print(document)
