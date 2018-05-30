"""
This command is useful if your library is itself a git repository.
You can use this command to issue git commands in your library
repository without having to change your current directory.

CLI Examples
^^^^^^^^^^^^

    - Check the status of the library repository:

    .. code::

        papis git status

    - Commit all changes:

    .. code::

        papis git commit -a
"""
import papis.commands
import papis.commands.run
import papis.config
import argparse
import logging

logger = logging.getLogger('git')


def run(folder, command=[]):
    return papis.commands.run.run(folder, command=["git"] + command)


class Command(papis.commands.Command):

    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "git",
            help="Run a git command in the library folder"
        )

        self.parser.add_argument(
            "commands",
            help="Commands",
            default="",
            nargs=argparse.REMAINDER,
            action="store"
        )

    def main(self):
        return run(papis.config.get("dir"), command=self.args.commands)
