"""

Cli
^^^
.. click:: papis.commands.rm:cli
    :prog: papis rm
"""
import papis
import papis.api
from papis.utils import confirm, text_area
import papis.config
import papis.document
import papis.cli
import papis.strings
import papis.database
import click
import logging
import os


def run(document, filepath=None):
    """Main method to the rm command
    """
    db = papis.database.get()
    if filepath is not None:
        os.remove(filepath)
        document['files'].remove(os.path.basename(filepath))
        document.save()
    else:
        papis.document.delete(document)
        db.delete(document)
    return


@click.command("rm")
@click.help_option('-h', '--help')
@papis.cli.query_option()
@click.option(
    "--file",
    help="Remove files from a document instead of the whole folder",
    is_flag=True,
    default=False
)
@click.option(
    "-f", "--force",
    help="Do not confirm removal",
    is_flag=True,
    default=False
)
def cli(
        query,
        file,
        force
        ):
    """Delete command for several objects"""
    documents = papis.database.get().query(query)
    logger = logging.getLogger('cli:rm')

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return 0

    document = papis.api.pick_doc(documents)
    if not document:
        return
    if file:
        filepath = papis.api.pick(
            document.get_files()
        )
        if not filepath:
            return
        if not force:
            toolbar = 'The file {0} would be removed'.format(filepath)
            if not confirm("Are you sure?", bottom_toolbar=toolbar):
                return
        click.echo("Removing %s..." % filepath)
        return run(
            document,
            filepath=filepath
        )
    else:
        if not force:
            toolbar = 'The folder {0} would be removed'.format(
                document.get_main_folder()
            )
            logger.warning("This document will be removed, check it")
            text_area(
                title=toolbar, text=document.dump(), lexer_name='yaml'
            )
            if not confirm("Are you sure?", bottom_toolbar=toolbar):
                return
        click.echo("Removing ...")
        return run(document)
