"""
This command is useful if your library is itself a `git <https://git-scm.com/>`__
repository. You can use this command to issue ``git`` commands in your library
repository without having to change your current directory.

Examples
^^^^^^^^

- Check the status of the library repository:

.. code::

    papis git status

- Commit all changes:

.. code::

    papis git commit -a

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.git:cli
    :prog: papis git
"""

import click

import papis.cli


@click.command("git", context_settings={"ignore_unknown_options": True})
@click.argument("arguments", metavar="<ARGUMENTS>", nargs=-1)
@click.help_option("--help", "-h")
@click.option(
    "--pick", "-p",
    help="Give a query to pick a document to run the command in its folder.",
    metavar="<QUERY>",
    type=str,
    default="")
@papis.cli.sort_option()
@papis.cli.doc_folder_option()
@papis.cli.all_option()
@click.pass_context
def cli(ctx: click.Context,
        arguments: list[str],
        pick: str,
        sort_field: str,
        sort_reverse: bool,
        doc_folder: tuple[str, ...],
        _all: bool) -> None:
    """Run git command in a library or document folder."""

    from papis.commands.run import cli as run_cli
    ctx.invoke(run_cli,
               run_command=arguments,
               pick=pick,
               sort_field=sort_field, sort_reverse=sort_reverse,
               prefix="git",
               doc_folder=doc_folder,
               _all=_all)
