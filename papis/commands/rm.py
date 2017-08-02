import papis
import sys
import os
import shutil
import papis.utils


class Rm(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "rm",
            help="Delete entry"
        )

        self.add_search_argument()

        self.parser.add_argument(
            "-f", "--force",
            help="Do not confirm removal",
            default=False,
            action="store_true"
        )

    def main(self):
        documents = papis.utils.get_documents_in_lib(
            self.get_args().lib,
            self.get_args().search
        )
        document = self.pick(documents) or sys.exit(0)
        folder = document.get_main_folder()
        if not self.args.force:
            if input("Are you sure? (Y/n): ") in ["N", "n"]:
                sys.exit(0)
        print("Removing %s..." % folder)
        shutil.rmtree(folder)
        papis.utils.clear_lib_cache()
