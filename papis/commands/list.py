"""
This command is to list contents of a library.

Examples
^^^^^^^^

 - List all document files associated will all entries:

    .. code:: bash

        papis list --file

    .. raw:: HTML

        <script type="text/javascript"
        src="https://asciinema.org/a/XwD0ZaUORoOonwDw4rXoQDkjZ.js"
        id="asciicast-XwD0ZaUORoOonwDw4rXoQDkjZ" async></script>

 - List all document year and title with custom formatting:

    .. code:: bash

        papis list --format '{doc[year]} {doc[title]}'

    .. raw:: HTML

        <script type="text/javascript"
        src="https://asciinema.org/a/NZ8Ii1wWYPo477CIL4vZhUqOy.js"
        id="asciicast-NZ8Ii1wWYPo477CIL4vZhUqOy" async></script>

 - List all documents according to the bibitem formatting (stored in a template
   file ``bibitem.template``):

    .. code:: bash

        papis list --template bibitem.template

    .. raw:: HTML

        <script type="text/javascript"
        src="https://asciinema.org/a/QZTBZ3tFfyk9WQuJ9WWB2UpSw.js"
        id="asciicast-QZTBZ3tFfyk9WQuJ9WWB2UpSw" async></script>

"""

import papis
import os
import sys
import papis.utils
import papis.downloaders.utils


class Command(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "list",
            help="List documents from a given library"
        )

        self.add_search_argument()

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
            help="List entries using a custom papis format, e.g."
                " '{doc[year] {doc[title]}",
            default=None,
            action="store"
        )

        self.parser.add_argument(
            "--template",
            help="Template file containing a papis format to list entries",
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
                return 1
            fd = open(self.args.template)
            self.args.format = fd.read()
            fd.close()
        if self.args.downloaders:
            for downloader in \
               papis.downloaders.utils.getAvailableDownloaders():
                print(downloader)
            return 0

        documents = papis.api.get_documents_in_lib(
            self.get_args().lib,
            self.get_args().search
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
                    papis.utils.format_doc(self.args.format, document)
                )
            else:
                print(document.get_main_folder())
