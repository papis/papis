"""This command edits the information of the documents.
The editor used is defined by the ``editor`` configuration setting.


Cli
^^^
.. click:: papis.commands.edit:cli
    :prog: papis edit
"""
import papis
import os
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


def run(document, wait=True, git=False):
    database = papis.database.get()
    papis.utils.general_open(document.get_info_file(), "editor", wait=wait)
    document.load()
    database.update(document)
    if git:
        papis.git.add_and_commit_resource(
            document.get_main_folder(),
            document.get_info_file(),
            "Update information for '{0}'".format(
                papis.document.describe(document)))


@click.command("edit")
@click.help_option('-h', '--help')
@papis.cli.query_option()
@papis.cli.doc_folder_option()
@papis.cli.git_option(help="Add changes made to the info file")
@click.option(
    "-n",
    "--notes",
    help="Edit notes associated to the document",
    default=False,
    is_flag=True)
@click.option(
    "--all", "_all",
    help="Edit all matching documents",
    default=False,
    is_flag=True)
@click.option(
    "-e",
    "--editor",
    help="Editor to be used",
    default=None)
def cli(query, doc_folder, git, notes, _all, editor):
    """Edit document information from a given library"""

    logger = logging.getLogger('cli:edit')

    if doc_folder:
        documents = [papis.document.from_folder(doc_folder)]
    else:
        documents = papis.database.get().query(query)

    if editor is not None:
        papis.config.set('editor', editor)

    if not _all:
        document = papis.pick.pick_doc(documents)
        documents = [document] if document else []

    if len(documents) == 0:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return 0

    for document in documents:
        if notes:
            logger.debug("Editing notes")
            if not document.has("notes"):
                logger.warning(
                    "The document selected has no notes attached, \n"
                    "creating a notes files"
                )
                document["notes"] = papis.config.get("notes-name")
                document.save()
            notesPath = os.path.join(
                document.get_main_folder(),
                document["notes"]
            )

            if not os.path.exists(notesPath):
                logger.info("Creating {0}".format(notesPath))
                open(notesPath, "w+").close()

            papis.api.edit_file(notesPath)
            if git:
                papis.git.add_and_commit_resource(
                    document.get_main_folder(),
                    document.get_info_file(),
                    "Update notes for '{0}'".format(
                        papis.document.describe(document)))

        else:
            run(document, git=git)
