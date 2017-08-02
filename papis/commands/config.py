import sys
import os
import re
import configparser
import papis.commands


class Command(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "config",
            help="Print configuration values"
        )

        self.parser.add_argument(
            "option",
            help="Variable to print",
            default="",
            action="store"
        )

    def main(self):
        option = self.args.option.split(".")
        self.logger.debug(option)
        if len(option) == 1:
            key = option[0]
            section = None
        elif len(option) == 2:
            section = option[0]
            key = option[1]
        self.logger.debug("key = %s, sec = %s" % (key, section))
        val = papis.config.get(key, section=section)
        print(val)
