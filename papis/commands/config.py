"""
The ``config`` command allows you to query the settings used by Papis on your
system.

The ``config`` command returns the value used by Papis. Therefore, if you
haven't customized some setting, it will return the default value. In contrast,
if you have customized it, it will return the value you set.

Let's say you want to see which ``dir`` setting your default library is using.
You can achieve this with:

.. code::

    papis config dir

If you wanted to see which ``dir`` the ``books`` library uses, you would do:

.. code::

    papis -l books config dir

With ``-l``, Papis selects a specific library (here, the "books" library). The 
rest works just as above.

Settings from a specific section in the configuration file can also be
accessed by adding a dot ``"."`` between the section and the setting name. For
example, if your ``books`` library is configured as a section, you can do:

.. code::

    papis config books.dir

This is equivalent to the above ``papis -l books config dir`` command.

For a more complex example, the :ref:`Bibtex` command has its own
configuration settings. These can be accessed through

.. code::

    papis config bibtex.default-read-bibfile
    > main.bib

You can find a list of all available settings in the configuration section
at :ref:`general-settings`. Commands and other plugins can define their own
settings, which are documented separately. To list the default values in a
given section, use

.. code::

    papis config --list-defaults bibtex

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

logger = logging.getLogger(__name__)


def run(option_string: str) -> Optional[str]:
    option = option_string.split(".")
    key = section = None
    if len(option) == 1:
        key = option[0]
    elif len(option) == 2:
        section = option[0]
        key = option[1]
    else:
        raise ValueError("unsupported option format: '{}'".format(option_string))

    logger.debug("key = %s, sec = %s", key, section)
    return papis.config.get(key, section=section)


def _run_with_log(option_string: str) -> Optional[str]:
    try:
        return run(option_string)
    except ValueError:
        logger.error(
            "options should be in a <section>.<key> or <key> format: got '%s'",
            option_string)
    except papis.exceptions.DefaultSettingValueMissing as exc:
        logger.error("\n%s", str(exc).strip("\n"))

    return None


@click.command("config")
@click.help_option("--help", "-h")
@click.argument("options", nargs=-1)
@click.option(
    "--json", "_json",
    help="Print multiple settings in a JSON format",
    default=False, is_flag=True)
@click.option(
    "--list-defaults", "list_defaults",
    help="List all default configuration settings in the given section",
    default=False, is_flag=True)
def cli(options: List[str],
        _json: bool,
        list_defaults: bool) -> None:
    """Print configuration values"""
    import colorama

    logger.debug("config options: %s", options)

    def format(key: str, value: Any) -> str:
        return (
            "{c.Style.BRIGHT}{key}{c.Style.NORMAL} "
            "= {c.Fore.GREEN}{value!r}{c.Style.RESET_ALL}"
            .format(c=colorama, key=key, value=value))

    if not list_defaults and len(options) == 1:
        # NOTE: a single option is printed directly for a bit of backwards
        # compatiblity and easier use in shell scripts, so remove with care!
        click.echo(_run_with_log(options[0]))
        return

    json_result = {}
    if list_defaults:
        defaults = papis.config.get_default_settings()
        for option in options:
            if option not in defaults:
                logger.error("Section '%s' has no defaults", option)
                continue

            if _json:
                json_result[option] = defaults[option]
            else:
                click.echo("[{}]".format(option))
                for key, value in defaults[option].items():
                    click.echo(format(key, value))

                if option != options[-1]:
                    click.echo("")
    else:
        for option in options:
            value = _run_with_log(option)
            if value is None:
                continue

            if _json:
                json_result[option] = value
            else:
                click.echo(format(option, value))

    if _json:
        import json
        click.echo(json.dumps(json_result, indent=2))
