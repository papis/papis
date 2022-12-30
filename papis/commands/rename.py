"""
Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.rename:cli
    :prog: papis rename
"""

import os
from typing import Optional

import click

import papis.cli
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

    cmd = ["git", "-C", folder] if git else []
    cmd += ["mv", folder, new_folder_path]

    import subprocess
    logger.debug("Running command '%s'.", cmd)
    subprocess.call(cmd)

    if git:
        papis.git.commit(
            new_folder_path,
            "Rename from '{}' to '{}'".format(folder, new_name))

    db.delete(document)
    logger.debug("New document folder: '%s'.", new_folder_path)
    document.set_folder(new_folder_path)
    db.add(document)


@click.command("rename")
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@papis.cli.git_option()
@papis.cli.sort_option()
@papis.cli.doc_folder_option()
def cli(query: str,
        git: bool,
        sort_field: Optional[str],
        doc_folder: str,
        sort_reverse: bool) -> None:
    """Rename entry"""
    documents = papis.cli.handle_doc_folder_query_sort(query,
                                                       doc_folder,
                                                       sort_field,
                                                       sort_reverse)
    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return
    document = documents[0]

    new_name = papis.tui.utils.prompt(
        "Enter new folder name:\n"
        ">",
        default=document.get_main_folder_name() or "")

    run(document, new_name, git=git)
