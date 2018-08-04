"""
This command is useful to issue commands in the directory of your library.

CLI Examples
^^^^^^^^^^^^

    - List files in your directory

    .. code::

        papis run ls

    - Find a file in your directory using the ``find`` command

    .. code::

        papis run find -name 'document.pdf'

Python examples
^^^^^^^^^^^^^^^

.. code::python

    from papis.commands.run import run

    run(library='papers', command=["ls", "-a"])

Cli
^^^
.. click:: papis.commands.run:cli
    :prog: papis run
"""
import os
import papis.config
import papis.exceptions
import logging
import click

logger = logging.getLogger('run')


def run(folder, command=[]):
    logger.debug("Changing directory into %s" % folder)
    os.chdir(os.path.expanduser(folder))
    try:
        commandstr = os.path.expanduser(
            papis.config.get("".join(command))
        )
    except papis.exceptions.DefaultSettingValueMissing:
        commandstr = " ".join(command)
    logger.debug("Command = %s" % commandstr)
    return os.system(commandstr)


@click.command(context_settings=dict(ignore_unknown_options=True))
@click.help_option('--help', '-h')
@click.argument("run_command", nargs=-1)
def cli(run_command):
    """Run an arbitrary shell command in the library folder"""
    folder = papis.config.get("dir")
    return run(folder, command=run_command)
