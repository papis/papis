"""
The ``mv`` command is used to organise a library moving their documents inside
subfolders, which can be optionally created from a format adapted to each
document.

It will (except when run with ``--all``) bring up the picker with a list of
documents that match the query. In the picker, you can select one or more
documents and then initiate renaming by pressing enter. Folder names are cleaned,
so that various characters (white spaces, punctuation, capital letters, and some
others) are automatically converted.

Examples
^^^^^^^^

- Query documents by author "Rick Astley" and move some of them. After picking
  the relevant documents, Papis will prompt you for the subfolder where they
  should be placed.

   .. code:: sh

        papis mv author:"Rick Astley"

- You can use ``--folder-name`` to pass in the subfolder they should be
  placed into, and ``--all`` to act on all documents that match the query.
  Here we'll move all documents by author "Rick Astley" into a subfolder named
  ``to_research``:

   .. code:: sh

        papis mv --folder-name to_research --all author:"Rick Astley"

- You can use formatting rules to generate the folder name too. For instance, to
  organise all documents by author "Rick Astley" by year, you can use (Python and
  Jinja2 formatting, respectively):

   .. code:: sh

        # Python format
        papis mv --folder-name "{doc[year]}" --all author:"Rick Astley"

        # Jinja2 format
        papis mv --folder-name "{{doc.year}}" --all author:"Rick Astley"

- If you want to rename all documents without narrowing down your selection in
  the picker, you can use the ``--all`` flag. Be careful when combining this
  with ``--batch``, as you might end up renaming a lot folders without
  confirmation:

   .. code:: sh

        papis rename --all author:"Rick Astley"

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.mv:cli
    :prog: papis mv
"""

import os
from typing import Optional, Tuple

import click

import papis.format
import papis.config
import papis.git
import papis.utils
import papis.database
import papis.document
import papis.cli
import papis.pick
import papis.strings
import papis.logging
import papis.tui.utils
from papis.exceptions import DocumentFolderNotFound

logger = papis.logging.get_logger(__name__)


def run(document: papis.document.Document,
        dest_path: str,
        git: bool = False) -> None:

    doc_main_folder = document.get_main_folder()
    if not doc_main_folder:
        raise DocumentFolderNotFound(papis.document.describe(document))

    if git:
        papis.git.mv(doc_main_folder, dest_path)
    else:
        import shutil
        shutil.move(doc_main_folder, dest_path)

    db = papis.database.get()
    db.delete(document)

    new_document_folder = os.path.join(dest_path,
                                       os.path.basename(doc_main_folder))
    logger.debug("New document folder: '%s'.", new_document_folder)

    document.set_folder(new_document_folder)
    db.add(document)


@click.command("mv")
@click.help_option("--help", "-h")
@click.option(
    "--folder-name",
    help="Name for the document's folder (papis format)"
    )
@papis.cli.query_argument()
@papis.cli.git_option()
@papis.cli.sort_option()
@papis.cli.doc_folder_option()
@papis.cli.all_option()
def cli(query: str,
        git: bool,
        _all: bool,
        folder_name: str,
        sort_field: Optional[str],
        doc_folder: Tuple[str, ...],
        sort_reverse: bool) -> None:
    """Move a document into another folder"""
    # Leave this imports here for performance
    import prompt_toolkit
    import prompt_toolkit.completion

    documents = papis.cli.handle_doc_folder_query_all_sort(query,
                                                           doc_folder,
                                                           sort_field,
                                                           sort_reverse,
                                                           _all
                                                           )
    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    lib_dir = os.path.expanduser(papis.config.get_lib_dirs()[0])
    completer = prompt_toolkit.completion.PathCompleter(
        only_directories=True,
        get_paths=lambda: [str(lib_dir)]
    )

    # If the user hasn't passed ``--folder_name``, we'll prompt for one that
    # will be used throughout the process.
    dest_path = None
    if folder_name is None:
        try:
            subfolder = prompt_toolkit.prompt(
                message="Destination folder: (Tab completion enabled)\n> ",
                completer=completer,
                complete_while_typing=True)
            dest_path = os.path.join(lib_dir, subfolder)
        except Exception as exc:
            logger.error("Failed to choose directory.", exc_info=exc)
            return

    if not git and os.path.exists(os.path.join(lib_dir, ".git")):
        git = papis.tui.utils.confirm("Add the changes to git?")

    moves = []
    for document in documents:
        # If the user has passed ``--folder-name``, use that to generate the subfolder
        if folder_name is not None:
            subfolder = papis.format.format(folder_name, document)
            dest_path = os.path.join(lib_dir, subfolder)

        # This should never be reached, but just in case.
        if dest_path is None:
            logger.error("Failed to construct a folder path for the document.")
            return

        # Check against erroneous documents
        doc_main_folder = document.get_main_folder()
        if not doc_main_folder:
            raise DocumentFolderNotFound(papis.document.describe(document))

        # This can happen when using format but a key doesn't exist and so the
        # format expression evaluates to ''.
        if dest_path.rstrip(os.path.sep) == os.path.dirname(doc_main_folder):
            logger.warning("Skipping '%s': its source and destination are the same",
                           doc_main_folder)
            continue

        if not os.path.exists(dest_path):
            logger.info("Creating path '%s'.", dest_path)
            os.makedirs(dest_path, mode=papis.config.getint("dir-umask") or 0o666)

        logger.info("Moving document from '%s' to the destination subfolder: '%s'.",
                    doc_main_folder, dest_path)

        moves.append((document, dest_path))

    for document, dest_path in moves:
        run(document, dest_path, git=git)
