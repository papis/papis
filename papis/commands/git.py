"""
This command is useful if your library is itself a git repository.
You can use this command to issue git commands in your library
repository without having to change your current directory.

Here are some examples of its usage:

    - Check the status of the library repository:

    .. code::

        papis git status

    - Commit all changes:

    .. code::

        papis git commit -a
"""
import papis.commands
import argparse


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
        run = papis.commands.get_commands("run")
        run.set_args(self.get_args())
        run.set_commands(["git"] + self.args.commands)
        run.main()
