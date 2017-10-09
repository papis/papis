"""
This command is useful to issue commands in the directory of your library.

Here are some examples of its usage:

    - List files in your directory

    .. code::

        papis run ls

    - Find a file in your directory using the ``find`` command

    .. code::

        papis run find -name 'document.pdf'
"""
import string
import os
import papis.config
import papis.exceptions
import argparse


class Command(papis.commands.Command):

    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "run",
            help="Run a command in the library folder"
        )

        self.parser.add_argument(
            "run_command",
            help="Command name or command",
            default="",
            nargs=argparse.REMAINDER,
            action="store"
        )

    def set_commands(self, commands):
        """Set commands to be run.
        :param commands: List of commands
        :type  commands: list
        """
        self.args.run_command = commands

    def main(self):
        lib_dir = os.path.expanduser(self.get_config()[self.args.lib]["dir"])
        self.logger.debug("Changing directory into %s" % lib_dir)
        os.chdir(lib_dir)
        try:
            command = os.path.expanduser(
                papis.config.get("".join(self.args.run_command))
            )
        except papis.exceptions.DefaultSettingValueMissing:
            command = " ".join(self.args.run_command)
        self.logger.debug("Command = %s" % command)
        command = string.Template(command).safe_substitute(
            self.get_config()[self.args.lib]
        )
        os.system(command)
