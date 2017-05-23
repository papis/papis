import sys
import os
import re
import configparser
import papis.commands


class Config(papis.commands.Command):
    def init(self):
        """TODO: Docstring for init.

        :subparser: TODO
        :returns: TODO

        """

        self.parser = self.get_subparsers().add_parser(
            "config",
            help="Manage the configuration options"
        )

        self.parser.add_argument(
            "option",
            help="Set or get option",
            default="",
            nargs="*",
            action="store"
        )

    def main(self, args):
        """
        Main action if the command is triggered

        :config: User configuration
        :args: CLI user arguments
        :returns: TODO

        """
        documentsDir = os.path.expanduser(self.config[args.lib]["dir"])
        self.logger.debug("Using directory %s" % documentsDir)
        # FIXME: Replacing values does not work
        option = " ".join(args.option)
        self.logger.debug(option)
        value = False
        m = re.match(r"([^ ]*)\.(.*)", option)
        if not m:
            self.logger.error("Syntax for option %s not recognised" % option)
            sys.exit(1)
        lib = m.group(1)
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
            if key in self.config[lib].keys():
                print(self.config[lib][key])
            else:
                sys.exit(1)
        else:
            try:
                self.config.remove_option(lib, key)
                self.config.set(lib, key, value)
            except configparser.NoSectionError:
                self.config.add_section(lib)
                self.config.set(lib, key, value)
            self.config.save()
