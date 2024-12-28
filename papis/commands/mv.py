"""
This command can be used to move a document to a new folder.

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.mv:cli
    :prog: papis mv
"""

import os
from typing import Optional, Tuple

import click

import papis.config
import papis.git
import papis.utils
import papis.database
import papis.document
import papis.cli
import papis.pick
import papis.strings
import papis.logging
from papis.exceptions import DocumentFolderNotFound

logger = papis.logging.get_logger(__name__)


def run(document: papis.document.Document,
        new_folder_path: str,
        git: bool = False) -> None:

    folder = document.get_main_folder()
    if not folder:
        raise DocumentFolderNotFound(papis.document.describe(document))

    if git:
        papis.git.mv(folder, new_folder_path)
    else:
        import shutil
        shutil.move(folder, new_folder_path)

    db = papis.database.get()
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
        sort_field: Optional[str],
        doc_folder: Tuple[str, ...],
        sort_reverse: bool) -> None:
    """Move a document into some other path"""
    # Leave this imports here for performance
    import prompt_toolkit
    import prompt_toolkit.completion

    documents = papis.cli.handle_doc_folder_query_sort(query,
                                                       doc_folder,
                                                       sort_field,
                                                       sort_reverse)
    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
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
