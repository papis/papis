"""
Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.rm:cli
    :prog: papis rm
"""

import os
from typing import Optional

import click

import papis.pick
import papis.tui.utils
import papis.document
import papis.cli
import papis.strings
import papis.database
import papis.git
import papis.logging
from papis.exceptions import DocumentFolderNotFound

logger = papis.logging.get_logger(__name__)


def run(document: papis.document.Document,
        filepath: Optional[str] = None,
        notespath: Optional[str] = None,
        git: bool = False) -> None:
    """Main method to the rm command
    """
    db = papis.database.get()
    _doc_folder = document.get_main_folder()
    if not _doc_folder:
        raise DocumentFolderNotFound(papis.document.describe(document))

    if filepath is not None:
        os.remove(filepath)
        document["files"].remove(os.path.basename(filepath))
        document.save()
        db.update(document)
        if git:
            papis.git.remove(_doc_folder, filepath)
            papis.git.add(_doc_folder, document.get_info_file())
            papis.git.commit(_doc_folder, "Remove file '{0}'".format(filepath))

    if notespath is not None:
        os.remove(notespath)
        del document["notes"]
        document.save()
        db.update(document)
        if git:
            papis.git.remove(_doc_folder, notespath)
            papis.git.add(_doc_folder, document.get_info_file())
            papis.git.commit(_doc_folder,
                             "Remove notes file '{}'".format(notespath))

    # if neither files nor notes were deleted -> delete whole document
    if not (filepath or notespath):
        if git:
            _topfolder = os.path.dirname(os.path.abspath(_doc_folder))
            papis.git.remove(_doc_folder, _doc_folder, recursive=True)
            papis.git.commit(
                _topfolder,
                "Remove document '{0}'".format(
                    papis.document.describe(document)))
        else:
            papis.document.delete(document)
        db.delete(document)


@click.command("rm")
@click.help_option("-h", "--help")
@papis.cli.query_argument()
@papis.cli.git_option(help="Remove in git")
@papis.cli.sort_option()
@papis.cli.doc_folder_option()
@click.option(
    "--file", "_file",
    help="Remove files from a document instead of the whole folder",
    is_flag=True,
    default=False)
@click.option(
    "-n", "--notes", "_notes",
    help="Remove the notes file from a document instead of the whole folder",
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
        _notes: bool,
        force: bool,
        _all: bool,
        doc_folder: str,
        sort_field: Optional[str],
        sort_reverse: bool) -> None:
    """
    Delete a document, a file, or a notes-file
    """

    documents = papis.cli.handle_doc_folder_query_all_sort(query,
                                                           doc_folder,
                                                           sort_field,
                                                           sort_reverse,
                                                           _all)
    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    if _file:
        for document in documents:
            filepaths = papis.pick.pick(document.get_files())
            if not filepaths:
                continue
            filepath = filepaths[0]
            if not force:
                tbar = "The file {0} would be removed".format(filepath)
                if not papis.tui.utils.confirm(
                        "Are you sure?", bottom_toolbar=tbar):
                    continue
            logger.info("Removing file '%s' from document.", filepath)
            run(document, filepath=filepath, git=git)

    if _notes:
        for document in documents:
            if "notes" not in document:
                continue
            notespath = os.path.join(
                str(document.get_main_folder()),
                document["notes"]
            )
            if not force:
                tbar = "The file {0} would be removed".format(notespath)
                if not papis.tui.utils.confirm(
                        "Are you sure?", bottom_toolbar=tbar):
                    continue
            logger.info("Removing notes: '%s'.", notespath)
            run(document, notespath=notespath, git=git)

    if not (_file or _notes):
        for document in documents:
            if not force:
                logger.warning("Removing folder: '%s'.", document.get_main_folder())
                logger.warning("The following document will be removed:")
                papis.tui.utils.text_area(
                    text=papis.document.dump(document),
                    lexer_name="yaml")
                if not papis.tui.utils.confirm(
                        "Do you want to remove the document?"):
                    continue

            run(document, git=git)
            logger.warning("Document removed: '%s'.", papis.document.describe(document))
