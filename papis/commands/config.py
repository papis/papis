"""
The ``config`` command is a useful command because it allows you to check
the configuration settings' values that your current `papis` session
is using.

For example let's say that you want to see which ``dir`` setting your
default library is using (i.e., the directory or the dir that appears
in the definition of the library in the configuration file), then you
would simply do

.. code::

    papis config dir

If you wanted to see which ``dir`` the ``books`` library has, for example,
then you would do

.. code::

    papis -l books config dir

This works equally for any default settings, i.e. settings that have not been
customized. For example, querying the ``match-format`` setting is done using

.. code::

    papis config match-format
    > {doc[tags]}{doc.subfolder}{doc[title]}{doc[author]}{doc[year]}

Settings from a specific section in the configuration file can also be
accessed by adding a dot ``"."`` between the section and the setting name. For
example, if your ``books`` library is configured as a section, you could
(equivalently) do

.. code::

    papis config books.dir

For a more complex example, the :ref:`Bibtex` command has its own
configuration settings. These can be accessed through

.. code::

    papis config bibtex.default-read-bibfile
    > main.bib

You can find a list of all available settings in the configuration section
at :ref:`general-settings`. Commands and other plugins can define their own
settings, which are documented separately.

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.config:cli
    :prog: papis config
"""

import logging
from typing import Any, List, Optional

import click

import papis.config
import papis.commands

logger = logging.getLogger("config:run")


def run(option_string: str) -> Optional[str]:
    option = option_string.split(".")
    key = section = None
    if len(option) == 1:
        key = option[0]
    elif len(option) == 2:
        section = option[0]
        key = option[1]
    else:
        logger.error(
            "options should be in a <section>.<key> or <key> format: got '%s'",
            option_string)
        return None

    logger.debug("key = %s, sec = %s", key, section)

    try:
        return papis.config.get(key, section=section)
    except papis.exceptions.DefaultSettingValueMissing as exc:
        logger.error("\n%s", str(exc).strip("\n"))

    return None


@click.command("config")
@click.help_option("--help", "-h")
@click.argument("options", nargs=-1)
@click.option(
    "--list-defaults", "list_defaults",
    help="List all default configuration settings in the given section",
    default=False, is_flag=True)
def cli(options: List[str],
        list_defaults: bool) -> None:
    """Print configuration values"""
    import colorama

    logger.debug("config options: %s", options)
    logger.info("Configuration file: '%s'", papis.config.get_config_file())

    def format(key: str, value: Any) -> str:
        return (
            "{c.Style.BRIGHT}{key}{c.Style.NORMAL} "
            "= {c.Fore.GREEN}{value!r}{c.Style.RESET_ALL}"
            .format(c=colorama, key=key, value=value))

    if list_defaults:
        defaults = papis.config.get_default_settings()
        for option in options:
            if option not in defaults:
                logger.error("Section '%s' has no defaults", option)
                continue

            click.echo("")
            click.echo("[{}]".format(option))
            for key, value in defaults[option].items():
                click.echo(format(key, value))
    else:
        for option in options:
            value = run(option)
            if value is not None:
                click.echo(format(option, value))
