"""
This command is to list contents of a library.
"""

import papis
import os
import sys
import papis.utils
import papis.downloaders.utils


class List(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "list",
            help="List documents from a given library"
        )

        self.parser.add_argument(
            "document",
            help="Document search",
            default="",
            nargs="?",
            action="store"
        )

        self.parser.add_argument(
            "-i",
            "--info",
            help="Show the info file name associated with the document",
            default=False,
            action="store_true"
        )

        self.parser.add_argument(
            "-f",
            "--file",
            help="Show the file name associated with the document",
            action="store_true"
        )

        self.parser.add_argument(
            "-d",
            "--dir",
            help="Show the folder name associated with the document",
            action="store_true"
        )

        self.parser.add_argument(
            "--format",
            help="List entries using special format",
            default=None,
            action="store"
        )

        self.parser.add_argument(
            "--template",
            help="Use template file for formating output",
            default=None,
            action="store"
        )

        self.parser.add_argument(
            "-p",
            "--pick",
            help="Pick the document instead of listing everything",
            action="store_true"
        )

        self.parser.add_argument(
            "--downloaders",
            help="List available downloaders",
            action="store_true"
        )

    def main(self):
        if self.args.template:
            if not os.path.exists(self.args.template):
                self.logger.error(
                    "Template file %s not found" % self.args.template
                )
                sys.exit(1)
            fd = open(self.args.template)
            self.args.format = fd.read()
            fd.close()
        if self.args.downloaders:
            for downloader in \
               papis.downloaders.utils.getAvailableDownloaders():
                print(downloader)
            sys.exit(0)
        documentsDir = os.path.expanduser(self.get_config()[self.args.lib]["dir"])
        self.logger.debug("Using directory %s" % documentsDir)
        documentSearch = self.args.document
        documents = papis.utils.get_documents_in_dir(
            documentsDir,
            documentSearch
        )
        if self.args.pick:
            documents = [self.pick(documents)]
        for document in documents:
            if self.args.file:
                for f in document.get_files():
                    print(f)
            elif self.args.info:
                print(
                    os.path.join(
                        document.get_main_folder(),
                        document.get_info_file()
                    )
                )
            elif self.args.format:
                print(
                    self.args.format.format(doc=document)
                )
            else:
                print(document.get_main_folder())
