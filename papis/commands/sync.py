"""
This is the command that can be used to synchronize libraries.
You can customize the sync command using the configuration setting
`sync-command`.

Examples of `sync-command` setting usage are:

    - For git compatibility, use for instance

    .. code::

        sync-command = git -C {lib[dir]} pull origin master

    - For rsync compatibility, use for instance

    .. code::

        sync-command = rsync -r some/remote/host {lib[dir]}

"""
import os
import string
import papis.commands
import papis.config
import papis.api


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
        command = sync_command.format(
            lib=self.get_config()[self.get_args().lib]
        )
        print(command)
        os.system(command)
        papis.api.clear_lib_cache()
