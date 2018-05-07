import papis
import os
import re
import papis.api
import papis.config
import papis.utils
import papis.database
import subprocess
import logging


def get_dirs(main):
    directories = []
    p = ""
    for root, dirs, files in os.walk(main):
        for di in dirs:
            p = os.path.join(root, di, papis.utils.get_info_file_name())
            if not os.path.exists(p) \
               and not re.match(r".*[.]git.*", os.path.join(root, di)):
                directories.append(di)
    return directories


def run(document, new_folder_path, git=False):
    logger = logging.getLogger('mv:run')
    folder = document.get_main_folder()
    cmd  = ['git', '-C', folder] if git else []
    cmd += ['mv', folder, new_folder_path]
    db = papis.database.get()
    logger.debug(cmd)
    subprocess.call(cmd)
    db.delete(document)
    new_document_folder = os.path.join(
        new_folder_path,
        os.path.basename(document.get_main_folder())
    )
    logger.debug("New document folder: {}".format(new_document_folder))
    document.set_folder(new_document_folder)
    db.add(document)


class Command(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "mv",
            help="Move entry"
        )

        self.add_search_argument()
        self.add_git_argument()

    def main(self):

        # Leave this imports here for performance
        import prompt_toolkit
        import prompt_toolkit.contrib.completers

        documents = self.get_db().query(self.args.search)

        document = self.pick(documents)
        if not document:
            return 0

        lib_dir = os.path.expanduser(papis.config.get('dir'))

        directories = get_dirs(lib_dir)

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

        run(document, new_folder, git=self.args.git)
