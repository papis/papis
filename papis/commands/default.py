import os
import sys
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
            "-c",
            "--config",
            help="Configuration file to use",
            default=None,
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

        self.default_parser.add_argument(
            "--clear-cache",
            help="Clear cache of the library used",
            action="store_true"
        )

        self.default_parser.add_argument(
            "-j", "--cores",
            help="Number of cores to run some multicore functionality",
            type=int,
            default=os.cpu_count(),
            action="store"
        )

    def main(self):
        self.set_args(papis.commands.get_args())
        log_format = '%(levelname)s:%(name)s:%(message)s'
        if self.args.verbose:
            self.args.log = "DEBUG"
            log_format = '%(relativeCreated)d-'+log_format
        logging.basicConfig(
            level=getattr(logging, self.args.log),
            format=log_format
        )

        if self.args.config:
            papis.config.set_config_file(self.args.config)
            papis.config.reset_configuration()
            papis.commands.Command.config = papis.config.get_configuration()

        if self.args.rofi:
            self.args.picktool = "rofi"

        if self.args.picktool:
            self.config["settings"]["picktool"] = self.args.picktool

        if self.args.pick_lib:
            self.args.lib = papis.utils.pick(papis.utils.get_libraries())

        if self.args.lib not in self.config.keys():
            if os.path.exists(self.args.lib):
                # Check if the path exists, then use this path as a new library
                self.logger.debug("Using library %s" % self.args.lib)
                self.config[self.args.lib] = dict()
                self.config[self.args.lib]["dir"] = self.args.lib
            else:
                self.logger.error(
                    "Library '%s' does not seem to exist" % self.args.lib
                )
                sys.exit(1)

        if self.args.clear_cache:
            papis.utils.clear_lib_cache(self.args.lib)

        commands = papis.commands.get_commands()

        if self.args.command:
            if self.args.command in commands.keys():
                commands[self.args.command].set_args(self.args)
                commands[self.args.command].main()
