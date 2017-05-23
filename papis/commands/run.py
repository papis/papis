import string
import os
import papis.config
from . import Command


class Run(Command):

    def init(self):
        self.subparser = self.parser.add_parser(
            "run",
            help="Run a command in the library folder"
        )
        self.subparser.add_argument(
            "run_command",
            help="Command name or command",
            default="",
            nargs="+",
            action="store"
        )

    def main(self, args):
        documentsDir = os.path.expanduser(self.config[self.args.lib]["dir"])
        self.logger.debug("Changing directory into %s" % documentsDir)
        os.chdir(documentsDir)
        try:
            command = os.path.expanduser(
                papis.config.get("".join(self.args.run_command))
            )
        except:
            command = " ".join(self.args.run_command)
        self.logger.debug("Command = %s" % command)
        command = string.Template(command).safe_substitute(
                self.config[self.args.lib])
        os.system(command)
