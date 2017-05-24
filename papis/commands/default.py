import string
import os
import papis.config
import papis.commands
import logging


class Default(papis.commands.Command):

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
            default=self.config["settings"]["default"] or "papers",
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

        self.default_parser.add_argument(
            "--picktool",
            help="Override picktool",
            action="store",
            default=""
        )

        self.default_parser.add_argument(
            "--rofi",
            help="Use rofi as a picktool",
            action="store_true"
        )

        self.default_parser.add_argument(
            "--pick-lib",
            help="Pick library to use",
            action="store_true"
        )


    def main(self):
        self.set_args(papis.commands.get_args())
        if self.args.verbose:
            self.args.log = "DEBUG"
        logging.basicConfig(level=getattr(logging, self.args.log))

        if self.args.rofi:
            self.args.picktool = "rofi"

        if self.args.picktool:
            self.config["settings"]["picktool"] = self.args.picktool

        if self.args.pick_lib:
            self.args.lib = papis.utils.pick(papis.utils.get_libraries())


        if self.args.lib not in self.config.keys():
            self.logger.error("Library '%s' does not seem to exist" % self.args.lib)
            sys.exit(1)

        commands = papis.commands.get_commands()

        if self.args.command:
            if self.args.command in commands.keys():
                commands[self.args.command].set_args(self.args)
                commands[self.args.command].main()
