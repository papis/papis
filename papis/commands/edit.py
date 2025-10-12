"""
This command edits the :ref:`info.yaml file <info-file>` of the documents.
The editor used is defined by the :confval:`editor` configuration
setting.

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.edit:cli
    :prog: papis edit
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import click

import papis.cli
import papis.config
import papis.logging

if TYPE_CHECKING:
    import papis.document

logger = papis.logging.get_logger(__name__)


def run(document: papis.document.Document,
        wait: bool = True,
        git: bool = False) -> None:
    from papis.document import describe, to_dict

    info_file_path = document.get_info_file()
    if not info_file_path:
        from papis.exceptions import DocumentFolderNotFound
        raise DocumentFolderNotFound(describe(document))

    old_dict = to_dict(document)

    from papis.utils import general_open
    general_open(info_file_path, "editor", wait=wait)

    document.load()
    new_dict = to_dict(document)

    # If nothing changed there is nothing else to be done
    if old_dict == new_dict:
        logger.debug("No changes made to the document.")
        return

    from papis.hooks import run as run_hook
    run_hook("on_edit_done", document)

    from papis.database import get_database
    db = get_database()
    db.update(document)

    if git:
        from papis.git import add_and_commit_resource
        add_and_commit_resource(
            str(document.get_main_folder()),
            info_file_path,
            f"Update information for '{describe(document)}'")


def edit_notes(document: papis.document.Document,
               git: bool = False) -> None:
    from papis.document import describe

    logger.debug("Editing notes.")
    notes = document.get("notes", None)

    if notes is not None and not isinstance(notes, str):
        logger.error(
            "Cannot edit notes! Ensure that a single relative file name "
            "is present in the 'info.yml' file.")
        logger.error("Notes have type '%s' not 'str': %s",
                     type(notes).__name__, describe(document))
        return

    from papis.notes import notes_path_ensured
    notes_path = notes_path_ensured(document)

    from papis.api import edit_file
    edit_file(notes_path)

    if git:
        from papis.git import add_and_commit_resources

        folder = document.get_main_folder()
        if folder:
            msg = f"Update notes for '{describe(document)}'"
            add_and_commit_resources(folder,
                                     [notes_path, document.get_info_file()],
                                     msg)


@click.command("edit")
@click.help_option("-h", "--help")
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@papis.cli.git_option(help="Add changes made to the info file.")
@papis.cli.sort_option()
@papis.cli.bool_flag(
    "-n", "--notes",
    help="Edit notes associated to the document.")
@papis.cli.all_option()
@click.option(
    "-e",
    "--editor",
    help="Editor to be used.",
    default=None)
def cli(query: str,
        doc_folder: tuple[str, ...],
        git: bool,
        notes: bool,
        _all: bool,
        editor: str | None,
        sort_field: str | None,
        sort_reverse: bool) -> None:
    """Edit document information from a given library."""
    documents = papis.cli.handle_doc_folder_query_all_sort(query,
                                                           doc_folder,
                                                           sort_field,
                                                           sort_reverse,
                                                           _all)
    if not documents:
        from papis.strings import no_documents_retrieved_message
        logger.warning(no_documents_retrieved_message)
        return

    if editor is not None:
        papis.config.set("editor", papis.config.escape_interp(editor))

    for document in documents:
        if notes:
            edit_notes(document, git=git)

        else:
            run(document, git=git)
