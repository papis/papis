"""
The ``rename`` command is used to rename document folders based on
a provided format or using :confval:`add-folder-name`.

Examples
^^^^^^^^

- Manually rename all folders for documents matching a query. ``papis`` will
  prompt for the new folder name, with the current name as a default.

   .. code:: sh

        papis rename author:"Rick Astley"

- Rename picked folders that match a query and automatically ``--folder-name``
  the names following the pattern provided by the ``add-folder-name``
  configuration option. It will ask for confirmation before each rename. It
  doesn't slugify the names, so if the pattern results in "Rick Astley - Never
  Gonna Give You Up", that will be the final folder name.

   .. code:: sh

        papis rename --folder-name author:"Rick Astley"

- Rename folders without asking for confirmation using ``--batch``.

   .. code:: sh

        papis rename -r --batch author:"Rick Astley"

- The folder names can be slugified too with the ``--slugify`` flag. This avoids
  uppercase or special characters, among others.  This can make it easier to type
  the names into a terminal, share them via a web or to make the folder names
  more portable.

   .. code:: sh

        papis rename -rb --slugify author:"Rick Astley"

- There is also an option to avoid picking the entries, ``--all``. This is
  a flag that should be used with caution, especially when used along with
  ``--batch``, since it will make ``papis rename`` act on all matching documents.
  To rename all matched folders with a name generated from config, "slugifying"
  the names and asking for confirmation before each rename:

   .. code:: sh

        papis rename -rbs --all author:"Rick Astley"


Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.rename:cli
    :prog: papis rename
"""

from typing import Optional, Tuple, List

import click

import papis.config
import papis.cli
import papis.format
import papis.utils
import papis.database
import papis.strings
import papis.git
import papis.pick
import papis.document
import papis.tui.utils
import papis.logging
from papis.exceptions import DocumentFolderNotFound

logger = papis.logging.get_logger(__name__)


def run(document: papis.document.Document,
        new_folder_name: str,
        git: bool = False) -> None:
    import os
    import shutil

    db = papis.database.get()
    folder = document.get_main_folder()

    if not folder:
        raise DocumentFolderNotFound(papis.document.describe(document))

    parent = os.path.dirname(folder)
    new_folder_path = os.path.join(parent, new_folder_name)
    logger.debug("New document folder: '%s'.", new_folder_path)

    if os.path.exists(new_folder_path):
        logger.warning("Path '%s' already exists.", new_folder_path)
        return

    if git:
        papis.git.mv_and_commit_resource(
            folder, new_folder_path,
            f"Rename '{folder}' to '{new_folder_name}'")
    else:
        shutil.move(folder, new_folder_path)

    db.delete(document)
    document.set_folder(new_folder_path)
    db.add(document)


def prepare_run(operations: List[Tuple[papis.document.Document, str]],
                git: bool
                ) -> None:
    for document, new_name in operations:
        run(document, new_name, git)


@click.command("rename")
@click.option(
    "--folder-name",
    help="Name for the document's folder (papis format)",
    default=lambda: papis.config.getstring("add-folder-name"))
@papis.cli.bool_flag("--batch", "-b", default=False, help="Batch mode, do not prompt")
@click.help_option("--help", "-h")
@papis.cli.all_option()
@papis.cli.query_argument()
@papis.cli.git_option()
@papis.cli.sort_option()
@papis.cli.doc_folder_option()
def cli(query: str,
        git: bool,
        folder_name: str,
        _all: bool,
        batch: bool,
        sort_field: Optional[str],
        doc_folder: Tuple[str, ...],
        sort_reverse: bool) -> None:
    """Rename document folders"""
    documents = papis.cli.handle_doc_folder_query_all_sort(query,
                                                           doc_folder,
                                                           sort_field,
                                                           sort_reverse,
                                                           _all
                                                           )
    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    renames = []
    for document in documents:
        current_name = document.get_main_folder_name()
        new_name = papis.format.format(folder_name, document)
        new_name = papis.utils.clean_document_name(new_name)

        if batch:
            logger.info("Renaming '%s' into '%s'", current_name, new_name)
        else:
            papis.tui.utils.confirm(f"Rename {current_name} into {new_name}?", True)

        renames.append((document, new_name))

    prepare_run(renames, git)
