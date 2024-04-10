"""
Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.rename:cli
    :prog: papis rename
"""

import os
from typing import Optional, Tuple

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


@click.command("rename")
@papis.cli.bool_flag("--batch", "-b", default=False, help="Batch mode, do not prompt")
@papis.cli.bool_flag("--slugify", "-s", default=False, help="Slugify the folder name")
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
        slugify: bool,
        sort_field: Optional[str],
        doc_folder: Tuple[str, ...],
        sort_reverse: bool) -> None:
    """Rename entry"""
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

    for document in documents:
        current_name = document.get_main_folder_name()
        if regenerate:
            new_name = papis.format.format(folder_name_pattern, document)
            if slugify:
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

        run(document, new_name, git=git)
