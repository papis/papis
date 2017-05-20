import string
import os
from . import Command


class Sync(Command):
    default_git = 'cd $dir; git pull origin master'

    def init(self):
        self.subparser = self.parser.add_parser(
            "sync",
            help="Sync a library using the sync command"
        )

    def main(self, args):
        documentsDir = os.path.expanduser(self.config[args.lib]["dir"])
        try:
            sync_command = os.path.expanduser(self.config[args.lib]["sync"])
        except KeyError:
            if os.path.exists(os.path.join(documentsDir, ".git", "config")):
                print("Git repository detected, using sync command '%s'"
                      % self.default_git)
                sync_command = self.default_git
        command = string.Template(sync_command).substitute(self.config[args.lib])
        os.system(command)
