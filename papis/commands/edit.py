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
import papis.utils
import papis.config
import papis.database
import papis.cli
import click
import logging


def run(document, editor=None, wait=True):
    if editor is not None:
        papis.config.set('editor', editor)
    database = papis.database.get()
    papis.utils.general_open(document.get_info_file(), "editor", wait=wait)
    document.load()
    database.update(document)


@click.command()
@click.help_option('-h', '--help')
@papis.cli.query_option()
@click.option(
    "-n",
    "--notes",
    help="Edit notes associated to the document",
    default=False,
    is_flag=True
)
@click.option(
    "--all",
    help="Edit all matching documents",
    default=False,
    is_flag=True
)
def cli(
        query,
        notes,
        all
        ):
    """Edit document information from a given library"""

    logger = logging.getLogger('cli:edit')
    documents = papis.database.get().query(query)
    if not all:
        document = papis.api.pick_doc(documents)
        documents = [document] if document else []

    if len(documents) == 0:
        return 0

    for document in documents:
        if notes:
            logger.debug("Editing notes")
            if not document.has("notes"):
                logger.warning(
                    "The document selected has no notes attached,"
                    " creating one..."
                )
                document["notes"] = papis.config.get("notes-name")
                document.save()
            notesPath = os.path.join(
                document.get_main_folder(),
                document["notes"]
            )
            if not os.path.exists(notesPath):
                logger.debug("Creating %s" % notesPath)
                open(notesPath, "w+").close()
            papis.api.edit_file(notesPath)
        else:
            run(document)
