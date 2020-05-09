"""
This command is useful if your library is itself a mercurial repository.
You can use this command to issue mercurial commands in your library
repository without having to change your current directory.

CLI Examples
^^^^^^^^^^^^

    - Check the status of the library repository:

    .. code::

        papis hg status

    - Commit all changes:

    .. code::

        papis hg commit


"""
import copy
import click
import papis.commands.run

cli = copy.deepcopy(papis.commands.run.cli)
cli.help = "Run hg command in a library or document folder"
cli = click.option("--prefix", hidden=True, default="hg", type=str)(cli)
