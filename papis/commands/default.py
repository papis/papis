import string
import os
import papis.config
import papis.commands
import logging
from . import Command


class Default(Command):

    def init(self):

        self.default_parser.add_argument(
            "-v",
            "--verbose",
            help="Make the output verbose (equivalent to --log DEBUG)",
            default=False,
            action="store_true"
        )

        self.default_parser.add_argument(
            "-l",
            "--lib",
            help="Choose a documents library, default general",
            default=config["settings"]["default"] or "papers",
            action="store"
        )

        self.default_parser.add_argument(
            "--log",
            help="Logging level",
            choices=[
                "INFO",
                "DEBUG",
                "WARNING",
                "ERROR",
                "CRITICAL"
                ],
            action="store",
            default="INFO"
        )


    def main(self, args):
        if self.args.verbose:
            self.args.log = "DEBUG"
        logging.basicConfig(level=getattr(logging, self.args.log))

        if self.args.lib not in self.config.keys():
            self.logger.error("Library '%s' does not seem to exist" % self.args.lib)
            sys.exit(1)

        if self.args.command:
            if self.args.command in subcommands.keys():
                subcommands[self.args.command].set_args(self.args)
                subcommands[self.args.command].main(self.args)
