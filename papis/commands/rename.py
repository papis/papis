"""
The ``rename`` command is used to rename document folders based on
a provided format or using :confval:`add-folder-name`.


Examples
^^^^^^^^

- Manually rename all folders for documents matching a query. ``papis`` will
  prompt for the new folder name, with the current name as a default.

   .. code:: sh

        papis rename author:"Rick Astley"

- Rename picked folders that match a query and automatically ``--regenerate``
  the names following the pattern provided by the ``add-folder-name``
  configuration option. It will ask for confirmation before each rename. It
  doesn't slugify the names, so if the pattern results in "Rick Astley - Never
  Gonna Give You Up", that will be the final folder name.

   .. code:: sh

        papis rename --regenerate author:"Rick Astley"

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


import os
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
        new_name: str, git: bool = False) -> None:
    db = papis.database.get()
    folder = document.get_main_folder()

    if not folder:
        raise DocumentFolderNotFound(papis.document.describe(document))

    subfolder = os.path.dirname(folder)
    new_folder_path = os.path.join(subfolder, new_name)

    if os.path.exists(new_folder_path):
        logger.warning("Path '%s' already exists.", new_folder_path)
        return

    papis.utils.run((["git"] if git else []) + ["mv", folder, new_folder_path],
                    cwd=folder)

    if git:
        papis.git.commit(
            new_folder_path,
            f"Rename from '{folder}' to '{new_name}'")

    db.delete(document)
    logger.debug("New document folder: '%s'.", new_folder_path)
    document.set_folder(new_folder_path)
    db.add(document)


def prepare_run(operations: List[Tuple[papis.document.Document, str]],
                git: bool
                ) -> None:
    for document, new_name in operations:
        run(document, new_name, git)


@click.command("rename")
@papis.cli.bool_flag("--batch", "-b", default=False, help="Batch mode, do not prompt")
@papis.cli.bool_flag("--regenerate", "-r", default=False,
                     help="Regenerate the folder name from the configured patttern")
@click.help_option("--help", "-h")
@papis.cli.all_option()
@papis.cli.query_argument()
@papis.cli.git_option()
@papis.cli.sort_option()
@papis.cli.doc_folder_option()
def cli(query: str,
        git: bool,
        regenerate: bool,
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

    if regenerate:
        folder_name_pattern = papis.config.getstring("add-folder-name")

    renames = []
    for document in documents:
        current_name = document.get_main_folder_name()
        if regenerate:
            new_name = papis.format.format(folder_name_pattern, document)
            new_name = papis.utils.clean_document_name(new_name)

            if batch:
                logger.info("Renaming '%s' into '%s'", current_name, new_name)
            else:
                papis.tui.utils.confirm(f"Rename {current_name} into {new_name}?", True)
        else:
            new_name = papis.tui.utils.prompt(
                "Enter new folder name:\n"
                ">",
                default=current_name or "")

        renames.append((document, new_name))

    prepare_run(renames, git)
