import papis
import os
import sys
import papis.api
import papis.utils


class Command(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "open",
            help="Open document from a given library"
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

        self.parser.add_argument(
            "--all",
            help="Open all matching documents",
            action="store_true"
        )

    def main(self):
        if self.args.tool:
            papis.config.set("opentool", self.args.tool)

        documents = papis.api.get_documents_in_lib(
            self.get_args().lib,
            self.args.search
        )
        if not documents:
            print("No documents found with that name.")
            return 1

        if not self.args.all:
            documents = [self.pick(documents)]
            documents = [d for d in documents if d]
            if not len(documents): return 0

        for document in documents:
            if not self.args.dir:
                files = document.get_files()
                file_to_open = papis.api.pick(
                    files,
                    pick_config=dict(
                        header_filter=lambda x: x.replace(
                            document.get_main_folder(), ""
                        )
                    )
                )
                papis.api.open_file(file_to_open)
            else:
                # Open directory
                papis.api.open_dir(document.get_main_folder())
