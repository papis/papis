"""

Cli
^^^
.. click:: papis.commands.rm:cli
    :prog: papis rm
"""
import papis
import papis.pick
import papis.utils
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
        db.update(document)
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
@click.option(
    "--all",
    help="Remove all matches",
    is_flag=True,
    default=False
)
def cli(
        query,
        file,
        force,
        all
        ):
    """Delete command for several objects"""
    documents = papis.database.get().query(query)
    logger = logging.getLogger('cli:rm')

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return 0

    if not all:
        documents = [papis.pick.pick_doc(documents)]
        documents = [d for d in documents if d]

    if file:
        for document in documents:
            filepath = papis.pick.pick(document.get_files())
            if not filepath:
                continue
            if not force:
                tbar = 'The file {0} would be removed'.format(filepath)
                if not papis.utils.confirm("Are you sure?", bottom_toolbar=tbar):
                    continue
            logger.info("Removing %s..." % filepath)
            run(
                document,
                filepath=filepath
            )
    else:
        for document in documents:
            if not force:
                tbar = 'The folder {0} would be removed'.format(
                    document.get_main_folder()
                )
                logger.warning("This document will be removed, check it")
                papis.utils.text_area(
                    title=tbar,
                    text=papis.document.dump(document),
                    lexer_name='yaml'
                )
                if not papis.utils.confirm("Are you sure?", bottom_toolbar=tbar):
                    continue
            logger.info("Removing ...")
            run(document)
