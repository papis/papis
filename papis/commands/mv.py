import papis
import sys
import os
import re
import papis.api
import papis.config
import papis.utils
import subprocess


class Command(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "mv",
            help="Move entry"
        )

        self.add_search_argument()
        self.add_git_argument()

    def get_dirs(self, main):
        directories = []
        p = ""
        for root, dirs, files in os.walk(main):
            for di in dirs:
                p = os.path.join(root, di, papis.utils.get_info_file_name())
                if not os.path.exists(p) \
                   and not re.match(r".*[.]git.*", os.path.join(root, di)):
                    directories.append(di)
        self.logger.debug(directories)
        return directories

    def main(self):

        # Leave this imports here for performance
        import prompt_toolkit
        import prompt_toolkit.contrib.completers

        documents = papis.api.get_documents_in_lib(
            self.get_args().lib,
            self.get_args().search
        )

        document = self.pick(documents)
        if not document: return 0

        lib_dir = os.path.expanduser(papis.config.get('dir'))
        folder = document.get_main_folder()

        directories = self.get_dirs(lib_dir)

        completer = prompt_toolkit.contrib.completers.WordCompleter(
            directories
        )

        try:
            new_folder = os.path.join(
                lib_dir,
                prompt_toolkit.prompt(
                    "Enter directory: (Tab completion enabled)\n"
                    ">  ",
                    completer=completer
                )
            )
        except:
            return 0

        self.logger.info(new_folder)

        if not os.path.exists(new_folder):
            self.logger.info("Creating path %s" % new_folder)
            os.makedirs(new_folder, mode=papis.config.getint('dir-umask'))

        mvtool = papis.config.get("mvtool")

        cmd = (['git', '-C', folder] if self.args.git else []) + \
            ['mv', folder, new_folder]
        self.logger.debug(cmd)
        subprocess.call(cmd)
        papis.api.clear_lib_cache()
