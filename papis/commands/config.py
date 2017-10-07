"""
The command config is a useful command because it allows you to check
the configuration settings' values that your current `papis` session
is using.

For example let's say that you want to see which ``dir`` setting your
current library is using (i.e., the directory or the dir that appears
in the definition of the library in the configuration file), then you
would simply do:

.. code::

    papis config dir

If you wanted to see which ``dir`` the library ``books`` has, for example
then you would do

.. code::

    papis -l books config dir

This works as well for default settings, i.e., settings that you have not
customized, for example the setting ``match-format``, you would check
it with

.. code::

    papis config match-format
    > {doc[tags]}{doc.subfolder}{doc[title]}{doc[author]}{doc[year]}

You can find a list of all available settings in the configuration section.


"""
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
