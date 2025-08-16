"""
This command edits the :ref:`info.yaml file <info-file>` of the documents.
The editor used is defined by the :confval:`editor` configuration
setting.

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.edit:cli
    :prog: papis edit
"""

import click

import papis
import papis.api
import papis.cli
import papis.config
import papis.database
import papis.document
import papis.format
import papis.git
import papis.hooks
import papis.logging
import papis.notes
import papis.pick
import papis.strings
import papis.utils
from papis.exceptions import DocumentFolderNotFound

logger = papis.logging.get_logger(__name__)


def run(document: papis.document.Document,
        wait: bool = True,
        git: bool = False) -> None:
    info_file_path = document.get_info_file()
    if not info_file_path:
        raise DocumentFolderNotFound(papis.document.describe(document))

    old_dict = papis.document.to_dict(document)
    papis.utils.general_open(info_file_path, "editor", wait=wait)
    document.load()
    new_dict = papis.document.to_dict(document)

    # If nothing changed there is nothing else to be done
    if old_dict == new_dict:
        logger.debug("No changes made to the document.")
        return

    papis.hooks.run("on_edit_done", document)
    papis.database.get().update(document)
    if git:
        papis.git.add_and_commit_resource(
            str(document.get_main_folder()),
            info_file_path,
            f"Update information for '{papis.document.describe(document)}'")


def edit_notes(document: papis.document.Document,
               git: bool = False) -> None:
    logger.debug("Editing notes.")
    notes = document.get("notes", None)
    if notes is not None and not isinstance(notes, str):
        logger.error(
            "Cannot edit notes! Ensure that a single relative file name "
            "is present in the 'info.yml' file.")
        logger.error("Notes have type '%s' not 'str': %s",
                     type(notes).__name__, papis.document.describe(document))
        return

    notes_path = papis.notes.notes_path_ensured(document)
    papis.api.edit_file(notes_path)
    if git:
        folder = document.get_main_folder()
        if folder:
            msg = f"Update notes for '{papis.document.describe(document)}'"
            papis.git.add_and_commit_resources(folder,
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
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    if editor is not None:
        papis.config.set("editor", papis.config.escape_interp(editor))

    for document in documents:
        if notes:
            edit_notes(document, git=git)

        else:
            run(document, git=git)
