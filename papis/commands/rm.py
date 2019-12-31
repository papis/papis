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
import papis.git
import click
import logging
import os


def run(document, filepath=None, git=False):
    """Main method to the rm command
    """
    db = papis.database.get()
    if filepath is not None:
        os.remove(filepath)
        document['files'].remove(os.path.basename(filepath))
        document.save()
        db.update(document)
        if git:
            papis.git.rm(document.get_main_folder(), filepath)
            papis.git.add(document.get_main_folder(), document.get_info_file())
            papis.git.commit(
                document.get_main_folder(),
                "Remove file '{0}'".format(filepath))
    else:
        if git:
            _topfolder = os.path.dirname(
                os.path.abspath(document.get_main_folder()))
            papis.git.rm(
                document.get_main_folder(), document.get_main_folder(),
                recursive=True)
            papis.git.commit(_topfolder,
                "Remove document '{0}'".format(
                    papis.document.describe(document)))
        else:
            papis.document.delete(document)
        db.delete(document)


@click.command("rm")
@click.help_option('-h', '--help')
@papis.cli.query_option()
@papis.cli.git_option(help="Remove in git")
@click.option(
    "--file",
    help="Remove files from a document instead of the whole folder",
    is_flag=True,
    default=False)
@click.option(
    "-f", "--force",
    help="Do not confirm removal",
    is_flag=True,
    default=False)
@papis.cli.all_option()
def cli(query, git, file, force, _all):
    """Delete a document or a file"""
    documents = papis.database.get().query(query)
    logger = logging.getLogger('cli:rm')

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return 0

    if not _all:
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
            run(document, filepath=filepath, git=git)
    else:
        for document in documents:
            if not force:
                tbar = 'The folder {0} would be removed'.format(
                    document.get_main_folder())
                logger.warning("This document will be removed, check it")
                papis.utils.text_area(
                    title=tbar,
                    text=papis.document.dump(document),
                    lexer_name='yaml')
                if not papis.utils.confirm("Are you sure?", bottom_toolbar=tbar):
                    continue
            logger.warning("removing ...")
            run(document, git=git)
