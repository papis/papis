"""
Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.rm:cli
    :prog: papis rm
"""

import os
from typing import Optional, Tuple

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
    doc_folder = document.get_main_folder()
    if not doc_folder:
        raise DocumentFolderNotFound(papis.document.describe(document))

    if filepath is not None:
        os.remove(filepath)
        document["files"].remove(os.path.basename(filepath))
        document.save()
        db.update(document)
        if git:
            papis.git.remove(doc_folder, filepath)
            papis.git.add(doc_folder, document.get_info_file())
            papis.git.commit(doc_folder, f"Remove file '{filepath}'")

    if notespath is not None:
        os.remove(notespath)
        del document["notes"]
        document.save()
        db.update(document)
        if git:
            papis.git.remove(doc_folder, notespath)
            papis.git.add(doc_folder, document.get_info_file())
            papis.git.commit(doc_folder,
                             f"Remove notes file '{notespath}'")

    # if neither files nor notes were deleted -> delete whole document
    if not (filepath or notespath):
        if git:
            topfolder = os.path.dirname(os.path.abspath(doc_folder))
            papis.git.remove(doc_folder, doc_folder, recursive=True)
            papis.git.commit(
                topfolder,
                "Remove document '{}'".format(papis.document.describe(document)))
        else:
            papis.document.delete(document)
        db.delete(document)


@click.command("rm")
@click.help_option("-h", "--help")
@papis.cli.query_argument()
@papis.cli.git_option(help="Remove in git")
@papis.cli.sort_option()
@papis.cli.doc_folder_option()
@papis.cli.bool_flag(
    "--file", "_file",
    help="Remove files from a document instead of the whole folder")
@papis.cli.bool_flag(
    "-n", "--notes", "_notes",
    help="Remove the notes file from a document instead of the whole folder")
@papis.cli.bool_flag(
    "-f", "--force",
    help="Do not confirm removal")
@papis.cli.all_option()
def cli(query: str,
        git: bool,
        _file: bool,
        _notes: bool,
        force: bool,
        _all: bool,
        doc_folder: Tuple[str, ...],
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
                tbar = f"The file {filepath} would be removed"
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
                tbar = f"The file {notespath} would be removed"
                if not papis.tui.utils.confirm(
                        "Are you sure?", bottom_toolbar=tbar):
                    continue
            logger.info("Removing notes: '%s'.", notespath)
            run(document, notespath=notespath, git=git)

    if not (_file or _notes):
        for document in documents:
            if not force:
                logger.warning("Removing folder: '%s'.", document.get_main_folder())
                papis.tui.utils.text_area(
                    text=papis.document.dump(document),
                    title="This document will be removed",
                    lexer_name="yaml")
                if not papis.tui.utils.confirm(
                        "Do you want to remove the document?"):
                    continue

            run(document, git=git)
            logger.warning("Document removed: '%s'.", papis.document.describe(document))
