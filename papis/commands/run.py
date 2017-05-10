import string
import os
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

    def main(self, config, args):
        documentsDir = os.path.expanduser(config[args.lib]["dir"])
        self.logger.debug("Changing directory into %s" % documentsDir)
        os.chdir(documentsDir)
        try:
            command = os.path.expanduser(
                config[args.lib]["".join(args.run_command)]
            )
        except:
            # print(config[args.lib][args.run_command])
            command = " ".join(args.run_command)
        self.logger.debug("Command = %s" % command)
        command = string.Template(command).safe_substitute(config[args.lib])
        os.system(command)
