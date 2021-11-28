"""This command edits the information of the documents.
The editor used is defined by the ``editor`` configuration setting.


Cli
^^^
.. click:: papis.commands.edit:cli
    :prog: papis edit
"""
import papis
import os
import papis.hooks
import papis.api
import papis.pick
import papis.document
import papis.utils
import papis.config
import papis.database
import papis.cli
import click
import logging
import papis.strings
import papis.git

from typing import Optional


def run(document: papis.document.Document,
        wait: bool = True,
        git: bool = False) -> None:
    database = papis.database.get()
    info_file_path = document.get_info_file()
    if not info_file_path:
        raise Exception(papis.strings.no_folder_attached_to_document)
    _old_dict = papis.document.to_dict(document)
    papis.utils.general_open(info_file_path, "editor", wait=wait)
    document.load()
    _new_dict = papis.document.to_dict(document)

    # If nothing changed there is nothing else to be done
    if _old_dict != _new_dict:
        return

    database.update(document)
    papis.hooks.run("on_edit_done")
    if git:
        papis.git.add_and_commit_resource(
            str(document.get_main_folder()),
            info_file_path,
            "Update information for '{0}'".format(
                papis.document.describe(document)))


def edit_notes(document: papis.document.Document,
               git: bool = False) -> None:
    logger = logging.getLogger('edit:notes')
    logger.debug("Editing notes")

    if not document.has("notes"):
        document["notes"] = papis.config.getstring("notes-name")
        document.save()
    notes_path = os.path.join(
        str(document.get_main_folder()),
        document["notes"]
    )

    if not os.path.exists(notes_path):
        logger.debug("Creating '%s'", notes_path)
        open(notes_path, "w+").close()

    papis.api.edit_file(notes_path)
    if git:
        papis.git.add_and_commit_resource(
            str(document.get_main_folder()),
            str(document.get_info_file()),
            "Update notes for '{0}'".format(
                papis.document.describe(document)))


@click.command("edit")
@click.help_option('-h', '--help')
@papis.cli.query_option()
@papis.cli.doc_folder_option()
@papis.cli.git_option(help="Add changes made to the info file")
@papis.cli.sort_option()
@click.option(
    "-n",
    "--notes",
    help="Edit notes associated to the document",
    default=False,
    is_flag=True)
@papis.cli.all_option()
@click.option(
    "-e",
    "--editor",
    help="Editor to be used",
    default=None)
def cli(query: str,
        doc_folder: str,
        git: bool,
        notes: bool,
        _all: bool,
        editor: Optional[str],
        sort_field: Optional[str],
        sort_reverse: bool) -> None:
    """Edit document information from a given library"""

    logger = logging.getLogger('cli:edit')

    if doc_folder:
        documents = [papis.document.from_folder(doc_folder)]
    else:
        documents = papis.database.get().query(query)

    if sort_field:
        documents = papis.document.sort(documents, sort_field, sort_reverse)

    if editor is not None:
        papis.config.set('editor', editor)

    if not _all:
        documents = list(papis.pick.pick_doc(documents))

    if len(documents) == 0:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    for document in documents:
        if notes:
            edit_notes(document, git=git)

        else:
            run(document, git=git)
