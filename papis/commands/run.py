r"""
This command is useful to issue commands in the directory of your library.

Examples
^^^^^^^^

    - List files in your directory

    .. code::

        papis run ls

    - Find a file in your directory using the ``find`` command

    .. code::

        papis run find -name 'document.pdf'

    - Find all pdfs in the document folders matching einstein

    .. code::

        papis run -p einstein --all -- find . -name '*.pdf'

      notice that in general, the symbol ``--`` is advisable
      so that the arguments after it are considered as positional arguments
      for the shell commands.

      In this example you could also use pipes, for instance to print the
      absolute path to the files, in linux you can use the command
      ``readlink -f`` and a pipe ``|`` to do this, i.e.:

    .. code::

        papis run -p einstein \
                --all -- "find . -name '*.pdf' | xargs readlink -f"

    - Replace some text in all info.yaml files by something.
      For instance imagine you want to replace all ``note`` field names
      in the ``info.yaml`` files by ``_note`` so that the ``note`` field
      does not get exported to bibtex. You can do

      .. code::

          papis run -a -- sed -i "s/^note:/_note:/" info.yaml


Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.run:cli
    :prog: papis run
"""

import os
from typing import List, Optional

import click

import papis.pick
import papis.cli
import papis.config
import papis.document
import papis.database
import papis.logging

logger = papis.logging.get_logger(__name__)


def run(folder: str, command: Optional[List[str]] = None) -> int:
    if command is None:
        command = []

    logger.debug("Changing directory to '%s'.", folder)
    os.chdir(os.path.expanduser(folder))
    commandstr = " ".join(command)

    logger.debug("Running command '%s'.", commandstr)
    return os.system(commandstr)


@click.command("run", context_settings={"ignore_unknown_options": True})
@click.help_option("--help", "-h")
@click.option(
    "--pick", "-p",
    help="Give a query to pick a document to run the command in its folder",
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
    help="Prefix shell commands by a prefix command")
@click.argument("run_command", metavar="<COMMANDS>", nargs=-1)
def cli(run_command: List[str],
        pick: str,
        sort_field: str,
        sort_reverse: bool,
        prefix: Optional[str],
        doc_folder: str,
        _all: bool) -> None:
    """Run an arbitrary shell command in the library or command folder"""

    documents = []

    if doc_folder:
        documents = [papis.document.from_folder(doc_folder)]
    elif pick:
        documents = papis.database.get().query(pick)

    if sort_field:
        documents = papis.document.sort(documents, sort_field, sort_reverse)

    if not _all and pick:
        documents = [d for d in papis.pick.pick_doc(documents)]

    if _all and not pick:
        documents = papis.database.get().get_all_documents()

    if documents:
        folders = [d for d in [d.get_main_folder() for d in documents] if d]
    else:
        folders = papis.config.get_lib_dirs()

    for folder in folders:
        run(folder, command=([prefix] if prefix else []) + list(run_command))
