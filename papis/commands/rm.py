"""

Cli
^^^
.. click:: papis.commands.rm:cli
    :prog: papis rm
"""
import click
import logging
import os

import papis.pick
import papis.tui.utils
import papis.document
import papis.cli
import papis.strings
import papis.database
import papis.git

from typing import Optional


def run(document: papis.document.Document,
        filepath: Optional[str] = None,
        git: bool = False) -> None:
    """Main method to the rm command
    """
    db = papis.database.get()
    _doc_folder = document.get_main_folder()
    if not _doc_folder:
        raise Exception(papis.strings.no_folder_attached_to_document)
    if filepath is not None:
        os.remove(filepath)
        document['files'].remove(os.path.basename(filepath))
        document.save()
        db.update(document)
        if git:
            papis.git.rm(_doc_folder, filepath)
            papis.git.add(_doc_folder, document.get_info_file())
            papis.git.commit(_doc_folder, "Remove file '{0}'".format(filepath))
    else:
        if git:
            _topfolder = os.path.dirname(os.path.abspath(_doc_folder))
            papis.git.rm(_doc_folder, _doc_folder, recursive=True)
            papis.git.commit(
                _topfolder,
                "Remove document '{0}'".format(
                    papis.document.describe(document)))
        else:
            papis.document.delete(document)
        db.delete(document)


@click.command("rm")
@click.help_option('-h', '--help')
@papis.cli.query_option()
@papis.cli.git_option(help="Remove in git")
@papis.cli.sort_option()
@papis.cli.doc_folder_option()
@click.option(
    "--file", "_file",
    help="Remove files from a document instead of the whole folder",
    is_flag=True,
    default=False)
@click.option(
    "-f", "--force",
    help="Do not confirm removal",
    is_flag=True,
    default=False)
@papis.cli.all_option()
def cli(query: str,
        git: bool,
        _file: bool,
        force: bool,
        _all: bool,
        doc_folder: str,
        sort_field: Optional[str],
        sort_reverse: bool) -> None:
    """Delete a document or a file"""

    if doc_folder:
        documents = [papis.document.from_folder(doc_folder)]
    else:
        documents = papis.database.get().query(query)

    if sort_field:
        documents = papis.document.sort(documents, sort_field, sort_reverse)

    logger = logging.getLogger('cli:rm')

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    if not _all:
        documents = list(papis.pick.pick_doc(documents))

    if _file:
        for document in documents:
            filepaths = papis.pick.pick(document.get_files())
            if not filepaths:
                continue
            filepath = filepaths[0]
            if not force:
                tbar = 'The file {0} would be removed'.format(filepath)
                if not papis.tui.utils.confirm(
                        "Are you sure?", bottom_toolbar=tbar):
                    continue
            logger.info("Removing %s..." % filepath)
            run(document, filepath=filepath, git=git)
    else:
        for document in documents:
            if not force:
                tbar = 'The folder {0} would be removed'.format(
                    document.get_main_folder())
                logger.warning("This document will be removed, check it")
                papis.tui.utils.text_area(
                    title=tbar,
                    text=papis.document.dump(document),
                    lexer_name='yaml')
                if not papis.tui.utils.confirm(
                        "Are you sure?", bottom_toolbar=tbar):
                    continue
            logger.warning("removing ...")
            run(document, git=git)
