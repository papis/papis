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
            "--file",
            help="Remove files from a document instead of the whole folder",
            default=False,
            action="store_true"
        )

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
        document = self.pick(documents)
        if not document: return 0
        if self.get_args().file:
            filepath = papis.api.pick(
                document.get_files()
            )
            if not filepath: return 0
            if not self.args.force:
                if not papis.utils.confirm("Are you sure?"):
                    return 0
            print("Removing %s..." % filepath)
            document.rm_file(filepath)
            document.save()
        else:
            folder = document.get_main_folder()
            if not self.args.force:
                if not papis.utils.confirm("Are you sure?"):
                    return 0
            print("Removing %s..." % folder)
            shutil.rmtree(folder)
            papis.api.clear_lib_cache()
