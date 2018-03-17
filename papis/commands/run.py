"""
This command is useful to issue commands in the directory of your library.

CLI Examples
^^^^^^^^^^^^

    - List files in your directory

    .. code::

        papis run ls

    - Find a file in your directory using the ``find`` command

    .. code::

        papis run find -name 'document.pdf'

Python examples
^^^^^^^^^^^^^^^

.. code::python

    from papis.commands.run import run

    run(library='papers', command=["ls", "-a"])

"""
import os
import papis.config
import papis.exceptions
import argparse
import logging

logger = logging.getLogger('run')


def run(folder, command=[]):
    logger.debug("Changing directory into %s" % folder)
    os.chdir(os.path.expanduser(folder))
    try:
        commandstr = os.path.expanduser(
            papis.config.get("".join(command))
        )
    except papis.exceptions.DefaultSettingValueMissing:
        commandstr = " ".join(command)
    logger.debug("Command = %s" % commandstr)
    return os.system(commandstr)


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
        folder = papis.config.get("dir")
        return run(folder, command=self.args.run_command)
