"""
Merge two documents.

The command uses the picker to select two documents. The first selected document
is the main document into which the second document will be merged. You will be prompted
whether you want to add any metadata, files and notes from the second document to the
first document.

Examples
^^^^^^^^

-   Pick duplicate documents:

    .. code:: sh

        papis merge "prediction and subs"

        /papers/de8d6373a8cef74b5245124ddb288d45-dejong-gerald
        /papers/0e378c330dba4a4483660388183aa648-dejong-gerald

    With the default picker and configuration, you can pick the two offending documents
    with ``CTRL+T``. The selected entries will have a ``#`` in the beginning of
    the document title.

    Papis will show the difference between the documents and let you select which
    changes to keep:

    .. code:: diff

        - collections: ['t3']
        + collections: ['t3', 't3a2']

    The lines are prefixed by an indication of what will happen on accepting the
    change. Papis will remove lines prefixed with a minus sign and add those
    with a plus sign.

    After deciding which metadata changes to apply, Papis will ask you decide which
    files of the second document to carry over into the first document. Files can be
    chosen by entering the numbers that precede them. If the second document has notes
    and the first doesn't, Papis will prompt you whether to carry those over as well.

-   Merge the documents that match the query "prediction and subs" and commit
    the changes to git:

    .. code:: sh

        papis merge --git "prediction and subs"

-   Keep both documents:

    .. code:: sh

        papis merge --keep "belief revision"

    Merging operates as it does in the standard case, but both documents are kept
    in the library.

-   Merge without prompting:

    .. code:: sh

        papis merge --batch "prediction and subs"

    The query has to match exactly two documents so the picker isn't needed. Metadata
    missing from the first document is filled in from the second. All the files from the
    second document are carried over to the first and so are its notes, should the first
    document not already contain any. Fields with conflicting values keep the value of
    the first document and are warned about.


Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.merge:cli
    :prog: papis merge
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import click

import papis.cli
import papis.logging

if TYPE_CHECKING:
    from papis.document import Document

logger = papis.logging.get_logger(__name__)


def run(a: Document,
        b: Document,
        data: dict[str, Any],
        files: list[str],
        notes: str | None,
        keep_both: bool,
        git: bool = False) -> None:
    """Apply the changes of a merge of *b* into *a*.

    :param data: metadata with which to update *a*.
    :param files: absolute paths of files to add to *a*.
    :param notes: absolute path of the note file to set as ``notes`` of *a*.
    :param keep_both: if *True*, *b* is left in the library.
    """
    import shutil

    from papis.document import describe

    to_folder = a.get_main_folder()
    if not to_folder:
        from papis.exceptions import DocumentFolderNotFound
        raise DocumentFolderNotFound(describe(a))

    from papis.paths import make_unique_file

    file_names = [*a.get("files", [])]
    for f in files:
        logger.info("Copying file '%s' to '%s'.", os.path.basename(f), to_folder)
        target = make_unique_file(os.path.join(to_folder, os.path.basename(f)))
        shutil.copy(f, target)
        file_names.append(os.path.basename(target))

    if file_names:
        a["files"] = file_names

    if notes:
        logger.info("Copying notes '%s' to '%s'.", os.path.basename(notes), to_folder)
        target = make_unique_file(os.path.join(to_folder, os.path.basename(notes)))
        shutil.copy(notes, target)
        a["notes"] = os.path.basename(target)

    from papis.commands.update import run as update
    update(a, data, git=git)

    if not keep_both:
        from papis.commands.rm import run as rm

        logger.info("Removing '%s'.", describe(b))
        rm(b, git=git)
    else:
        logger.info("Keeping both documents.")


@click.command("merge")
@click.help_option("-h", "--help")
@papis.cli.query_argument()
@papis.cli.sort_option()
@papis.cli.bool_flag(
    "-s", "--second",
    help="Reverse the merge order (the default merges the second document"
         " into the first).")
@papis.cli.bool_flag(
    "-b", "--batch",
    help="Do not prompt. The merge proceeds automatically.")
@papis.cli.bool_flag(
    "-k", "--keep", "keep_both",
    help="Keep both documents.")
@papis.cli.git_option(help="Merge in git.")
def cli(query: str,
        sort_field: str | None,
        second: bool,
        batch: bool,
        git: bool,
        keep_both: bool,
        sort_reverse: bool) -> None:
    """Merge two documents from a given library."""
    from papis.database import get_database

    db = get_database()
    documents = db.query(query)

    from papis.document import describe, sort, to_dict

    if sort_field:
        documents = sort(documents, sort_field, sort_reverse)

    if not documents:
        from papis.strings import no_documents_retrieved_message
        logger.warning(no_documents_retrieved_message)
        return

    if not batch:
        from papis.pick import pick_doc
        documents = pick_doc(documents)

    if len(documents) != 2:
        logger.error(
            "You have to pick exactly two documents (got %d)!",
            len(documents))
        return

    # NOTE: `b` is merged into `a`
    if second:
        documents.reverse()
    a, b = documents

    logger.info(
        "Merging document B into A:\n  A: %s\n  B: %s",
        a.get_main_folder(), b.get_main_folder())

    data_a = to_dict(a)
    data_b = to_dict(b)

    to_pop = ["files", "notes", "papis_id"]
    for d in (data_a, data_b):
        for k in to_pop:
            if k in d:
                d.pop(k)

    if not batch:
        from papis.utils import update_doc_from_data_interactively
        logger.info("Select the metadata changes of B to apply to A.")
        update_doc_from_data_interactively(data_a, data_b, describe(b))

    from papis.tui.utils import confirm, select_range

    b_files = b.get_files()
    b_notes = b.get_notes()
    b_notes = b_notes[0] if b_notes else None
    notes: str | None = None
    if batch:
        conflicting = sorted(
            key
            for key in data_b
            if data_a.get(key) and data_b.get(key) and data_a[key] != data_b[key]
        )
        if conflicting:
            logger.warning(
                "Keeping the values of A for conflicting fields: %s",
                ", ".join(conflicting),
            )
        data_a.update({
            k: v for k, v in data_b.items() if data_b.get(k) and not data_a.get(k)
        })
        files = b_files
        notes = b_notes if not a.get("notes") else None
    else:
        if b_files:
            logger.info("Document B has files.")
        indices = select_range(b_files, "Files of B to keep", accept_none=True)
        files = [b_files[i] for i in indices]

        if b_notes and not a.get("notes"):
            logger.info("Document B has notes.")
            if confirm("Add the notes of B to A?"):
                notes = b_notes

    dropped_files = [f for f in b_files if f not in set(files)]
    if dropped_files and not keep_both:
        listed = "\n".join(f"  {os.path.basename(f)}" for f in dropped_files)
        logger.warning(
            "These files of B will be removed with the document folder:\n%s",
            listed)

    if b_notes and not notes and not keep_both:
        logger.warning(
            "The note of B will be removed with the document folder.")

    if not batch and not confirm("Are you sure you want to merge?"):
        return

    run(a, b, data_a, files, notes, keep_both, git)
