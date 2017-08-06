import papis
import sys
import os
import shutil
import papis.api
import papis.utils


class Command(papis.commands.Command):
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
        documents = papis.api.get_documents_in_lib(
            self.get_args().lib,
            self.get_args().search
        )
        document = self.pick(documents) or sys.exit(0)
        folder = document.get_main_folder()
        if not self.args.force:
            if not papis.utils.confirm("Are you sure?"):
                sys.exit(0)
        print("Removing %s..." % folder)
        shutil.rmtree(folder)
        papis.api.clear_lib_cache()
