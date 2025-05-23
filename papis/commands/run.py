r"""
This command can be used to run shell commands in the directory of your library.

Examples
^^^^^^^^

- List all files in the library directory:

    .. code:: sh

        papis run ls

- Find a file in the library directory using the ``find`` command:

    .. code:: sh

        papis run find -name 'document.pdf'

- Find all PDFs in the document folders matching "einstein":

    .. code:: sh

        papis run -p einstein --all -- find . -name '*.pdf'

    In general, the symbol ``--`` is advisable so that the arguments after it
    are considered as positional arguments for the shell commands.

    In this example you could also use pipes. For instance, to print the
    absolute path to the files, in Linux you can use the command
    ``readlink -f`` and a pipe ``|`` to do this, i.e.:

    .. code:: sh

        papis run -p einstein \
                --all -- "find . -name '*.pdf' | xargs readlink -f"

- Replace some text in all ``info.yaml`` files by something.
  For instance imagine you want to replace all ``note`` field names
  in the ``info.yaml`` files by ``_note`` so that the ``note`` field
  does not get exported. You can do:

    .. code:: sh

        papis run -a -- sed -i 's/^note:/_note:/' info.yaml


Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.run:cli
    :prog: papis run
"""

from typing import List, Optional, Tuple

import click

import papis.pick
import papis.cli
import papis.utils
import papis.config
import papis.document
import papis.database
import papis.logging

logger = papis.logging.get_logger(__name__)


def run(folder: str, command: Optional[List[str]] = None) -> None:
    if command is None:
        return

    papis.utils.run(command, cwd=folder, wait=True)


@click.command("run", context_settings={"ignore_unknown_options": True})
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
@click.option(
    "--prefix",
    default=None,
    type=str,
    metavar="<PREFIX>",
    help="Prefix shell commands by a prefix command.")
@click.argument("run_command", metavar="<COMMANDS>", nargs=-1)
def cli(run_command: List[str],
        pick: str,
        sort_field: str,
        sort_reverse: bool,
        prefix: Optional[str],
        doc_folder: Tuple[str, ...],
        _all: bool) -> None:
    """Run an arbitrary shell command in the library or command folder."""

    documents = []

    if doc_folder:
        documents = [papis.document.from_folder(d) for d in doc_folder]
    elif pick:
        documents = papis.database.get().query(pick)

    if sort_field:
        documents = papis.document.sort(documents, sort_field, sort_reverse)

    if not _all and pick:
        documents = papis.pick.pick_doc(documents)

    if _all and not pick:
        documents = papis.database.get().get_all_documents()

    if documents:
        folders = [d for d in [d.get_main_folder() for d in documents] if d]
    else:
        folders = papis.config.get_lib_dirs()

    for folder in folders:
        cmd = ([prefix] if prefix else []) + list(run_command)
        run(folder, cmd)
