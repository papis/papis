"""
The ``mv`` command is used to move document folders around your library (or to
another library).

It will (except when run with ``--all``) bring up the picker with a list of
documents that match the query. You can then select the document or documents
you'd like to move. The command works similar to the POSIX mv command. Hence,
when the specified target folder exists (or ends with a `/`), the document's
current main folder is moved into the target folder. If the specified target
folder doesn't exist, then the current folder is renamed to the target folder
name. Folder names are cleaned, so that various problematic characters (white
spaces, punctuation, capital letters, and some others) are avoided.

Examples
^^^^^^^^

- Query documents by author "Rick Astley" and move some of them. After picking
  the relevant documents, they will be renamed to their default names
  specified by the `add-folder-name` option.

   .. code:: sh

        papis mv author:"Rick Astley"

- You can use ``--to`` to pass the name of the target folder. Here we'll move a
  document by the author "Rick Astley" to a folder named ``rick_astley``:

   .. code:: sh

        papis mv --to rick_astley author:"Rick Astley"

- You can use formatting rules to generate the folder names. For instance, to
  organise all documents by author "Rick Astley" by year, you can use a format
  pattern. Note that because of the flag ``--all`` this command will move
  all documents matching the query.

   .. code:: sh

        papis mv --to "{doc[year]}" --all author:"Rick Astley"

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.mv:cli
    :prog: papis mv
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import click

import papis.cli
import papis.config
import papis.database
import papis.document
import papis.git
import papis.logging
import papis.paths
import papis.tui.utils
from papis.exceptions import DocumentFolderNotFound
from papis.strings import AnyString, FormatPattern, no_documents_retrieved_message

if TYPE_CHECKING:
    from papis.document import Document

logger = papis.logging.get_logger(__name__)


def run(
    document: Document,
    doc_folder_new: str,
    doc_folder_old: str,
    batch: bool,
    target_lib_dir: str,
    target_library: str,
    git: bool = False,
) -> None:
    import shutil

    source_lib_dir = os.path.expanduser(papis.config.getstring(key="dir")).rstrip(
        os.path.sep
    )

    if os.path.exists(doc_folder_new):
        logger.warning("Target path '%s' already exists.", doc_folder_new)
        if not batch:
            confirm_overwrite = papis.tui.utils.confirm("Overwrite the folder?")
            if confirm_overwrite:
                shutil.rmtree(doc_folder_new)
            else:
                return
        else:
            return

    if target_lib_dir == source_lib_dir:
        # TODO: there was some mention of committing if tracked? can i just do
        #       the below or do i need to check if it's tracked?
        if git:
            os.makedirs(
                os.path.dirname(doc_folder_new),
                mode=papis.config.getint("dir-umask") or 511,
                exist_ok=True,
            )
            papis.git.mv_and_commit_resource(
                doc_folder_old,
                doc_folder_new,
                f"Move '{papis.document.describe(document)}'",
            )
        else:
            shutil.move(doc_folder_old, doc_folder_new)
    else:
        if git:
            # TODO: should I add a remove+commit helper function to papis.git?
            papis.git.remove(source_lib_dir, doc_folder_old)
            papis.git.commit(
                source_lib_dir, f"Remove '{papis.document.describe(document)}'"
            )

        shutil.move(doc_folder_old, doc_folder_new)

        if git and os.path.exists(os.path.join(target_lib_dir, ".git")):
            papis.git.add_and_commit_resource(
                target_lib_dir,
                doc_folder_new,
                f"Add '{papis.document.describe(document)}'",
            )

    source_db = papis.database.get()
    source_db.delete(document)

    logger.debug("New document folder: '%s'.", doc_folder_new)

    target_db = papis.database.get(library_name=target_library)

    document.set_folder(doc_folder_new)

    target_db.add(document)

    logger.info(
        "Moved document '%s' to '%s'.",
        papis.document.describe(document),
        doc_folder_new,
    )


@click.command("mv")
@click.help_option("--help", "-h")
@click.option(
    "-t",
    "--to",
    help="Target path. Uses POSIX mv semantics.",
    default=lambda: papis.config.getformatpattern("add-folder-name"),
    type=papis.cli.FormatPatternParamType(),
)
@click.option(
    "--target-library",
    help="Target library",
    default=papis.config.get_lib_name,
    type=str,
)
@papis.cli.bool_flag("-b", "--batch", help="Batch mode, do not prompt or otherwise.")
@papis.cli.query_argument()
@papis.cli.git_option()
@papis.cli.sort_option()
@papis.cli.doc_folder_option()
@papis.cli.all_option()
def cli(
    query: str,
    git: bool,
    _all: bool,
    to: AnyString,
    target_library: str,
    batch: bool,
    sort_field: str | None,
    doc_folder: tuple[str, ...],
    sort_reverse: bool,
) -> None:
    """Move a document into another folder"""

    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder, sort_field, sort_reverse, _all
    )
    if not documents:
        logger.warning(no_documents_retrieved_message)
        return

    target_lib_dir = os.path.expanduser(
        papis.config.getstring(key="dir", section=target_library)
    ).rstrip(os.path.sep)

    if not git and os.path.exists(os.path.join(target_lib_dir, ".git")):
        git = papis.tui.utils.confirm("Add the changes to git?")

    moves = []
    for document in documents:
        main_folder_old = document.get_main_folder()
        if not main_folder_old:
            raise DocumentFolderNotFound(papis.document.describe(document))

        # Determine operation mode
        if isinstance(to, FormatPattern):
            folder_name_format = to
        else:
            target_abs_path = papis.paths.get_document_folder(
                document, target_lib_dir, folder_name_format=to
            )

            is_move_into = to.endswith("/") or os.path.isdir(target_abs_path)

            if is_move_into:
                main_folder_new = os.path.join(to, os.path.split(main_folder_old)[1])

                folder_name_format = FormatPattern(None, main_folder_new)
            else:
                folder_name_format = FormatPattern(None, to)

        main_folder_new = papis.paths.get_document_folder(
            document, target_lib_dir, folder_name_format=folder_name_format
        )

        # Skip if source and destination are the same
        if main_folder_new.rstrip(os.path.sep) == main_folder_old.rstrip(os.path.sep):
            logger.warning(
                "Skipping '%s': its source and destination are the same",
                papis.document.describe(document),
            )
            continue

        # Check if target directory contains info file
        info_name = papis.config.getstring("info-name")
        main_folder_new_parent = os.path.dirname(main_folder_new)
        target_info_path = os.path.join(main_folder_new_parent, info_name)
        logger.debug("Target info path: '%s'.", target_info_path)
        if os.path.exists(target_info_path):
            logger.warning(
                "Target directory '%s' contains an '%s' and appears to be "
                "another document's folder.",
                main_folder_new_parent,
                info_name,
            )
            # TODO: not sure what to do here re handling of batch.
            # Maybe we do want 'batch' and 'force'?
            # - batch: run without prompts but safely
            # - force: force specified operation even if unsafe
            # We could do it here first and then adjust other commands
            if not batch:
                confirm = papis.tui.utils.confirm(
                    "Do you want to move the document into this folder?", yes=False
                )
                if not confirm:
                    logger.info(
                        "Skipping document '%s'.",
                        papis.document.describe(document),
                    )
                    continue
            else:
                logger.info(
                    "Skipping document '%s' in batch mode.",
                    papis.document.describe(document),
                )
                continue

        moves.append((document, main_folder_old, main_folder_new))

    for document, main_folder_old, main_folder_new in moves:
        run(
            document,
            main_folder_new,
            main_folder_old,
            batch=batch,
            git=git,
            target_lib_dir=target_lib_dir,
            target_library=target_library,
        )
