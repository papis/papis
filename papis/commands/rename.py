import papis
import sys
import os
import re
import papis.api
import papis.utils
import subprocess


class Command(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "rename",
            help="Rename entry"
        )

        self.add_search_argument()
        self.add_git_argument()


    def main(self):

        documents = papis.api.get_documents_in_lib(
            self.get_args().lib,
            self.get_args().search
        )

        document = self.pick(documents)
        if not document: return 0

        folder = document.get_main_folder()
        subfolder = os.path.dirname(folder)

        new_folder = os.path.join(
            subfolder,
            papis.utils.clean_document_name(
                papis.utils.input(
                    "Enter new folder name:\n"
                    ">",
                    default=document.get_main_folder_name()
                )
            )
        )

        self.logger.debug(new_folder)

        if os.path.exists(new_folder):
            self.logger.warning("Path %s already exists" % new_folder)
            return 1

        mvtool = papis.config.get("mvtool")

        cmd = (['git', '-C', folder] if self.args.git else []) + \
            ['mv', folder, new_folder]
        self.logger.debug(cmd)
        subprocess.call(cmd)
        papis.utils.git_commit(message="Rename %s" % folder)
        papis.api.clear_lib_cache()
