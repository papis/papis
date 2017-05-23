import readline
import papis
import sys
import os
import re
import papis.utils
import subprocess
from . import Command


class Mv(Command):
    def init(self):

        self.subparser = self.parser.add_parser(
            "mv",
            help="Move entry"
        )

        self.subparser.add_argument(
            "document",
            help="Document search",
            nargs="?",
            default=".",
            action="store"
        )

        self.subparser.add_argument(
            "-t", "--tool",
            help="Move tool",
            action="store"
        )

    def get_dirs(self, main):
        directories = []
        p = ""
        for root, dirs, files in os.walk(main):
            for di in dirs:
                p = os.path.join(root, di, papis.utils.getInfoFileName())
                if not os.path.exists(p) \
                   and not re.match(r".*[.]git.*", os.path.join(root, di)):
                    directories.append(di)
        self.logger.debug(directories)
        return directories

    def completer(self, text, state, values):
        options = [x for x in values if x.startswith(text)]
        try:
            return options[state]
        except IndexError:
            return None

    def main(self, args):
        """
        Main action if the command is triggered

        :config: User configuration
        :args: CLI user arguments
        :returns: TODO

        """
        documentsDir = os.path.expanduser(self.config[args.lib]["dir"])
        self.logger.debug("Using directory %s" % documentsDir)
        documentSearch = args.document
        documents = papis.utils.get_documents_in_dir(
            documentsDir,
            documentSearch
        )
        document = self.pick(documents)
        if not document:
            sys.exit(0)
        folder = document.getMainFolder()

        directories = self.get_dirs(documentsDir)
        readline.set_completer(
            lambda text, state: self.completer(text, state, directories)
        )
        readline.parse_and_bind("tab: complete")

        print("Enter directory: (Tab completion enabled)")
        new_folder = os.path.join(documentsDir, input("dir: "))
        self.logger.info(new_folder)
        if not os.path.exists(new_folder):
            self.logger.info("Creating path %s" % new_folder)
            os.makedirs(new_folder)
        if args.tool:
            mvtool = args.tool
        elif "mvtool" in self.config[args.lib].keys():
            mvtool = self.config[args.lib]["mvtool"]
        elif "mvtool" in self.config["settings"].keys():
            mvtool = self.config["settings"]["mvtool"]
        else:
            mvtool = "mv"

        cmd = [mvtool, folder, new_folder]
        self.logger.debug(cmd)
        subprocess.call(cmd)
