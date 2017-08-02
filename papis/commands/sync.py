import os
import string
import papis.commands
import papis.config


class Command(papis.commands.Command):

    def init(self):
        self.parser = self.get_subparsers().add_parser(
            "sync",
            help="Sync a library using the sync command"
        )

    def main(self):
        sync_command = os.path.expanduser(
            papis.config.get("sync-command")
        )
        command = string.Template(sync_command).substitute(
            self.get_config()[self.args.lib]
        )
        print(command)
        os.system(command)
