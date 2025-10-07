"""
A simple command that can remove entire Papis documents from your library or
just remove files within a document.

This command should be used with care, since it will remove the document from
your filesystem, not just from Papis' database.

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.rm:cli
    :prog: papis rm
"""

import os
from typing import TYPE_CHECKING

import click

import papis.cli
import papis.logging

if TYPE_CHECKING:
    import papis.document

logger = papis.logging.get_logger(__name__)


def run(document: "papis.document.Document",
        filepath: str | None = None,
        notespath: str | None = None,
        git: bool = False) -> None:
    """Main method to the rm command."""

    from papis.database import get_database
    db = get_database()
    doc_folder = document.get_main_folder()

    from papis.document import delete, describe

    if not doc_folder:
        from papis.exceptions import DocumentFolderNotFound
        raise DocumentFolderNotFound(describe(document))

    from papis.git import add as git_add, commit as git_commit, remove as git_rm

    if filepath is not None:
        os.remove(filepath)
        document["files"].remove(os.path.basename(filepath))
        document.save()
        db.update(document)
        if git:
            git_rm(doc_folder, filepath)
            git_add(doc_folder, document.get_info_file())
            git_commit(doc_folder, f"Remove file '{filepath}'")

    if notespath is not None:
        os.remove(notespath)
        del document["notes"]
        document.save()
        db.update(document)
        if git:
            git_rm(doc_folder, notespath)
            git_add(doc_folder, document.get_info_file())
            git_commit(doc_folder, f"Remove notes file '{notespath}'")

    # if neither files nor notes were deleted -> delete whole document
    if not (filepath or notespath):
        if git:
            topfolder = os.path.dirname(os.path.abspath(doc_folder))
            git_rm(doc_folder, doc_folder, recursive=True)
            git_commit(
                topfolder,
                f"Remove document '{describe(document)}'")
        else:
            delete(document)

        db.delete(document)


@click.command("rm")
@click.help_option("-h", "--help")
@papis.cli.query_argument()
@papis.cli.git_option(help="Remove in git.")
@papis.cli.sort_option()
@papis.cli.doc_folder_option()
@papis.cli.bool_flag(
    "--file", "_file",
    help="Remove files from a document instead of the whole folder.")
@papis.cli.bool_flag(
    "-n", "--notes", "_notes",
    help="Remove the notes file from a document instead of the whole folder.")
@papis.cli.bool_flag(
    "-f", "--force",
    help="Do not confirm removal.")
@papis.cli.all_option()
def cli(query: str,
        git: bool,
        _file: bool,
        _notes: bool,
        force: bool,
        _all: bool,
        doc_folder: tuple[str, ...],
        sort_field: str | None,
        sort_reverse: bool) -> None:
    """
    Remove a document, a file, or a notes-file.
    """

    documents = papis.cli.handle_doc_folder_query_all_sort(query,
                                                           doc_folder,
                                                           sort_field,
                                                           sort_reverse,
                                                           _all)
    if not documents:
        from papis.strings import no_documents_retrieved_message
        logger.warning(no_documents_retrieved_message)
        return

    from papis.tui.utils import confirm, text_area

    if _file:
        from papis.pick import pick

        for document in documents:
            filepaths = pick(document.get_files())
            if not filepaths:
                continue
            filepath = filepaths[0]
            if not force:
                tbar = f"The file {filepath} would be removed"
                if not confirm("Are you sure?", bottom_toolbar=tbar):
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
                if not confirm("Are you sure?", bottom_toolbar=tbar):
                    continue
            logger.info("Removing notes: '%s'.", notespath)
            run(document, notespath=notespath, git=git)

    if not (_file or _notes):
        from papis.document import describe, dump

        for document in documents:
            if not force:
                logger.warning("Removing folder: '%s'.", document.get_main_folder())
                text_area(
                    text=dump(document),
                    title="This document will be removed",
                    lexer_name="yaml")
                if not confirm("Do you want to remove the document?"):
                    continue

            run(document, git=git)
            logger.warning("Document removed: '%s'.", describe(document))
