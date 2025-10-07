"""
This command can be used to move a document to a new folder.

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.mv:cli
    :prog: papis mv
"""

import os
from typing import TYPE_CHECKING

import click

import papis.cli
import papis.config
import papis.logging

if TYPE_CHECKING:
    import papis.document

logger = papis.logging.get_logger(__name__)


def run(document: "papis.document.Document",
        new_folder_path: str,
        git: bool = False) -> None:
    from papis.document import describe

    folder = document.get_main_folder()
    if not folder:
        from papis.exceptions import DocumentFolderNotFound
        raise DocumentFolderNotFound(describe(document))

    if git:
        from papis.git import mv as git_mv
        git_mv(folder, new_folder_path)
    else:
        import shutil
        shutil.move(folder, new_folder_path)

    from papis.database import get_database
    db = get_database()
    db.delete(document)

    new_document_folder = os.path.join(
        new_folder_path,
        os.path.basename(folder))
    logger.debug("New document folder: '%s'.", new_document_folder)

    document.set_folder(new_document_folder)
    db.add(document)


@click.command("mv")
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@papis.cli.git_option()
@papis.cli.sort_option()
@papis.cli.doc_folder_option()
def cli(query: str,
        git: bool,
        sort_field: str | None,
        doc_folder: tuple[str, ...],
        sort_reverse: bool) -> None:
    """Move a document into some other path."""
    # Leave this imports here for performance
    import prompt_toolkit
    import prompt_toolkit.completion

    documents = papis.cli.handle_doc_folder_query_sort(query,
                                                       doc_folder,
                                                       sort_field,
                                                       sort_reverse)
    if not documents:
        from papis.strings import no_documents_retrieved_message
        logger.warning(no_documents_retrieved_message)
        return

    document = documents[0]

    lib_dir = os.path.expanduser(papis.config.get_lib_dirs()[0])

    completer = prompt_toolkit.completion.PathCompleter(
        only_directories=True,
        get_paths=lambda: [lib_dir]
    )

    try:
        new_folder = os.path.join(
            lib_dir,
            prompt_toolkit.prompt(
                message=(
                    "Enter directory  : (Tab completion enabled)\n"
                    f"Current directory: ({document.get_main_folder_name()})\n >"),
                completer=completer,
                complete_while_typing=True
            ))
    except Exception as exc:
        logger.error("Failed to choose directory.", exc_info=exc)
        return

    logger.info("New document folder: '%s'.", new_folder)

    if not os.path.exists(new_folder):
        logger.info("Creating path '%s'.", new_folder)
        os.makedirs(new_folder, mode=papis.config.getint("dir-umask") or 0o666)

    run(document, new_folder, git=git)
