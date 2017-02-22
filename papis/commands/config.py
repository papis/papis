
from ..document import Document
import papis
import sys
import os
import re
import papis.utils
from . import Command

class Config(Command):
    def init(self):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """

        config_parser = parser.add_parser(
                "config",
                help="Manage the configuration options"
                )

        config_parser.add_argument(
                "option",
                help="Set or get option",
                default="",
                nargs="*",
                action="store"
                )


    def main(self, config, args):
        """
        Main action if the command is triggered

        :config: User configuration
        :args: CLI user arguments
        :returns: TODO

        """
        documentsDir = os.path.expanduser(config[args.lib]["dir"])
        self.logger.debug("Using directory %s"%documentsDir)
        # FIXME: Replacing values does not work
        option = " ".join(args.option)
        self.logger.debug(option)
        value = False
        m = re.match(r"([^ ]*)\.(.*)", option)
        if not m:
            raise Exception("Syntax for option %s not recognised"%option)
        lib    = m.group(1)
        preKey = m.group(2)
        m = re.match(r"(.*)\s*=\s*(.*)", preKey)
        if m:
            key = m.group(1)
            value = m.group(2)
        else:
            key = preKey
        self.logger.debug("lib -> %s" % lib)
        self.logger.debug("key -> %s" % key)
        if not value:
            print(config[lib][key])
        else:
            try:
                config.remove_option(lib,key)
                config.set(lib, key, value)
            except configparser.NoSectionError:
                config.add_section(lib)
                config.set(lib, key, value)
            config.save()
