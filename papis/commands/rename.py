"""
The ``rename`` command is used to rename document folders based on
a provided format or using :confval:`add-folder-name`.

It will (except when run with ``--all``) bring up the picker with a list of
documents that match the query. In the picker, you can select one or more
documents and then initiate renaming by pressing enter. Folder names are cleaned,
so that various characters (white spaces, punctuation, capital letters, and some
others) are automatically converted.

Examples
^^^^^^^^

- Rename folders for documents whose author is "Rick Astley". You can then either
  enter a new folder name or accept Papis' suggestion. The suggested folder name
  will be generated according to :confval:`add-folder-name` or, if this option
  isn't set, the current folder name.

   .. code:: sh

        papis rename author:"Rick Astley"

- You can use ``--folder-name`` to pass in your desired name. This option
  supports Papis formatting patterns. You will be asked for confirmation
  before the folder is renamed.

   .. code:: sh

        papis rename --folder-name "{doc[author]}-never-gonna" author:"Rick Astley"

  This will give you a folder named "rick-astley-never-gonna".


- To stop Papis from asking for confirmation, use the ``--batch`` flag:

   .. code:: sh

        papis rename --batch author:"Rick Astley"

- If you want to rename all documents without narrowing down your selection in
  the picker, you can use the ``--all`` flag. Be careful when combining this
  with ``--batch``, as you might end up renaming a lot folders without
  confirmation:

   .. code:: sh

        papis rename --all author:"Rick Astley"

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.rename:cli
    :prog: papis rename
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import click

import papis.cli
import papis.config
import papis.logging

if TYPE_CHECKING:
    from papis.document import Document
    from papis.strings import AnyString

logger = papis.logging.get_logger(__name__)


def run(document: Document,
        new_folder_name: str,
        git: bool = False) -> None:
    import os
    import shutil

    from papis.database import get_database
    db = get_database()
    folder = document.get_main_folder()

    from papis.document import describe

    if not folder:
        from papis.exceptions import DocumentFolderNotFound
        raise DocumentFolderNotFound(describe(document))

    parent = os.path.dirname(folder)
    new_folder_path = os.path.join(parent, new_folder_name)

    if os.path.exists(new_folder_path):
        logger.warning("Path '%s' already exists.", new_folder_path)
        return

    logger.info("Rename '%s' to '%s'.", folder, new_folder_name)
    if git:
        from papis.git import mv_and_commit_resource
        mv_and_commit_resource(
            folder, new_folder_path,
            f"Rename '{folder}' to '{new_folder_name}'")
    else:
        shutil.move(folder, new_folder_path)

    db.delete(document)
    document.set_folder(new_folder_path)
    db.add(document)


@click.command("rename")
@click.help_option("-h", "--help")
@click.option(
    "--folder-name",
    help="Name format for the document main folder.",
    type=papis.cli.FormatPatternParamType(),
    default=lambda: papis.config.getformatpattern("add-folder-name"))
@papis.cli.bool_flag(
    "-b", "--batch",
    help="Batch mode, do not prompt.")
@papis.cli.all_option()
@papis.cli.query_argument()
@papis.cli.git_option()
@papis.cli.sort_option()
@papis.cli.doc_folder_option()
def cli(query: str,
        folder_name: AnyString,
        _all: bool,
        batch: bool,
        git: bool,
        sort_field: str | None,
        doc_folder: tuple[str, ...],
        sort_reverse: bool) -> None:
    """Rename document folders."""
    if not folder_name:
        logger.warning("No folder name format specified, so no documents can be "
                       "renamed. Set either the configuration option "
                       "'add-folder-name' or use the '--folder-name' flag.")
        return

    documents = papis.cli.handle_doc_folder_query_all_sort(query,
                                                           doc_folder,
                                                           sort_field,
                                                           sort_reverse,
                                                           _all
                                                           )
    if not documents:
        from papis.strings import no_documents_retrieved_message
        logger.warning(no_documents_retrieved_message)
        return

    from papis.format import format
    from papis.paths import normalize_path
    from papis.tui.utils import confirm

    renames = []
    for document in documents:
        current_name = document.get_main_folder_name()
        new_name = format(folder_name, document)
        new_name = normalize_path(new_name)

        if not batch and not confirm(f"Rename '{current_name}' to '{new_name}'?"):
            continue

        renames.append((document, new_name))

    # FIXME: these need to be done separately because the db.delete+db.add
    # messes with the documents in some way (it's all mostly in place)
    for document, new_name in renames:
        run(document, new_name, git=git)
