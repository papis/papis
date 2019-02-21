"""
This command is useful if your library is itself a git repository.
You can use this command to issue git commands in your library
repository without having to change your current directory.

CLI Examples
^^^^^^^^^^^^

    - Check the status of the library repository:

    .. code::

        papis git status

    - Commit all changes:

    .. code::

        papis git commit -a


"""
import papis.commands
import papis.commands.run
import papis.config
import logging
import click

logger = logging.getLogger('git')


def run(folder, command=[]):
    return papis.commands.run.run(folder, command=["git"] + command)


@click.command(context_settings=dict(ignore_unknown_options=True))
@click.help_option('--help', '-h')
@click.argument("command", nargs=-1)
def cli(command):
    "Run a git command in the library folder"
    return run(papis.config.get("dir"), command=list(command))
