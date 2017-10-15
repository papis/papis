import os
import sys
import papis
import papis.api
import papis.config
import papis.commands
import logging


class Command(papis.commands.Command):

    def init(self):

        self.default_parser.add_argument(
            "-v",
            "--verbose",
            help="Make the output verbose (equivalent to --log DEBUG)",
            default=False,
            action="store_true"
        )

        self.default_parser.add_argument(
            "-V",
            "--version",
            help="Show version number",
            default=False,
            action="store_true"
        )

        self.default_parser.add_argument(
            "-l",
            "--lib",
            help="Choose a library name or library path (unamed library)",
            default=papis.config.get("default-library"),
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
            "--pick-lib",
            help="Pick library to use",
            action="store_true"
        )

        self.default_parser.add_argument(
            "--clear-cache", "--cc",
            help="Clear cache of the library used",
            action="store_true"
        )

        self.default_parser.add_argument(
            "-j", "--cores",
            help="Number of cores to run some multicore functionality",
            type=int,
            default=__import__("multiprocessing").cpu_count(),
            action="store"
        )

        self.default_parser.add_argument(
            "--set",
            help="Set key value, e.g., "
                 "--set 'info-name = \"information.yaml\"  opentool = evince'",
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

        if self.args.version:
            print('Papis - %s' % papis.__version__)
            return 0

        if self.args.set:
            key_vals = papis.utils.DocMatcher.parse(self.args.set)
            self.logger.debug('Parsed set %s' % key_vals)
            for pair in key_vals:
                if len(pair) != 3:
                    continue
                key = pair[0]
                val = pair[2]
                papis.config.set(key, val)

        if self.args.config:
            papis.config.set_config_file(self.args.config)
            papis.config.reset_configuration()
            papis.commands.Command.config = papis.config.get_configuration()

        if self.args.picktool:
            papis.config.set("picktool", self.args.picktool)

        if self.args.pick_lib:
            self.args.lib = papis.api.pick(
                papis.api.get_libraries(),
                pick_config=dict(header_filter=lambda x: x)
            )

        if self.args.lib not in self.get_config().keys():
            if os.path.exists(self.args.lib):
                # Check if the path exists, then use this path as a new library
                self.logger.debug("Using library %s" % self.args.lib)
                self.get_config()[self.args.lib] = dict()
                self.get_config()[self.args.lib]["dir"] = self.args.lib
            else:
                self.logger.error(
                    "Library '%s' does not seem to exist" % self.args.lib
                )
                return 1

        if self.args.clear_cache:
            papis.api.clear_lib_cache(self.args.lib)

        commands = papis.commands.get_commands()

        if self.args.command:
            if self.args.command in commands.keys():
                commands[self.args.command].set_args(self.args)
                commands[self.args.command].main()
