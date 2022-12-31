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

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.config:cli
    :prog: papis config
"""

from typing import Optional

import click

import papis.commands
import papis.logging

logger = papis.logging.get_logger(__name__)


def run(option_string: str) -> Optional[str]:

    option = option_string.split(".")
    key = section = None
    if len(option) == 1:
        key = option[0]
    elif len(option) == 2:
        section = option[0]
        key = option[1]
    else:
        raise ValueError("unrecognized option: {}".format(option_string))

    logger.debug("key = %s, sec = %s", key, section)
    val = papis.config.get(key, section=section)

    return val


@click.command("config")
@click.help_option("--help", "-h")
@click.argument("option")
def cli(option: str) -> None:
    """Print configuration values"""
    logger.debug(option)

    click.echo(run(option))
