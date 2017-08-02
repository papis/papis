import papis
import os
import sys
import papis.utils


class Command(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "open",
            help="Open document document from a given library"
        )

        self.add_search_argument()

        self.parser.add_argument(
            "--tool",
            help="Tool for opening the file (opentool)",
            default="",
            action="store"
        )

        self.parser.add_argument(
            "-d",
            "--dir",
            help="Open directory",
            action="store_true"
        )

    def main(self):
        if self.args.tool:
            papis.config.set("opentool", self.args.tool)

        documents = papis.utils.get_documents_in_lib(
            self.get_args().lib,
            self.args.search
        )
        if not documents:
            print("No documents found with that name.")
            sys.exit(1)

        document = self.pick(documents)
        if not document:
            sys.exit(0)

        if not self.args.dir:
            files = document.get_files()
            file_to_open = papis.utils.pick(
                files,
                pick_config=dict(
                    header_filter=lambda x: x.replace(
                        document.get_main_folder(), ""
                    )
                )
            )
            papis.utils.open_file(file_to_open)
        else:
            # Open directory
            papis.utils.open_dir(document.get_main_folder())
