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

    def main(self):
        documentsDir = os.path.expanduser(
            self.get_config()[self.args.lib]["dir"]
        )
        self.logger.debug("Using directory %s" % documentsDir)
        # FIXME: Replacing values does not work
        option = " ".join(self.args.option)
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
            if key in self.get_config()[lib].keys():
                print(self.get_config()[lib][key])
            else:
                sys.exit(1)
        else:
            try:
                self.get_config().remove_option(lib, key)
                self.get_config().set(lib, key, value)
            except configparser.NoSectionError:
                self.get_config().add_section(lib)
                self.get_config().set(lib, key, value)
            self.get_config().save()
