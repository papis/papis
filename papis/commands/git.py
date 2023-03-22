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
import copy

import click

import papis.commands.run

cli = copy.deepcopy(papis.commands.run.cli)
cli.name = "git"
cli.help = "Run git command in a library or document folder"
cli = click.option("--prefix", hidden=True, default="git", type=str)(cli)
