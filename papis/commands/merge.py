"""
Merge two documents.

The command uses the picker to select two documents. The first selected document
is the main document into which the second document will be merged. You will be asked
whether you want to add any metadata, files and notes from the second document to the
first document.

Examples
^^^^^^^^

-   Pick duplicate documents:

    .. code:: sh

        papis merge "prediction and subs"

        /papers/de8d6373a8cef74b5245124ddb288d45-dejong-gerald
        /papers/0e378c330dba4a4483660388183aa648-dejong-gerald

    With the default Papis picker, you can mark the two offending documents using
    the :confval:`mark_key` (``ctrl-t`` by default). Marked entries are prefixed
    with a ``#`` in the document title.

    Papis will show the difference between the documents and let you select which
    changes to keep:

    .. code:: diff

        - collections: ['t3']
        + collections: ['t3', 't3a2']

    The lines are prefixed by an indication of what will happen on accepting the
    change. Papis will remove lines prefixed with a minus sign and add those
    with a plus sign.

    After deciding which metadata changes to apply, Papis will ask you to decide which
    files of the second document to carry over into the first document. Files can be
    chosen by entering the numbers that precede them. If the second document has notes,
    Papis will prompt you whether to carry those over as well, replacing the notes of
    the first document if it has any.

-   Merge the documents that match the query "prediction and subs" and commit
    the changes to git:

    .. code:: sh

        papis merge --git "prediction and subs"

-   Keep both documents:

    .. code:: sh

        papis merge --keep "belief revision"

    By default, the second document is removed after the merge. With this flag, it
    is kept.

-   Reverse the merge order:

    .. code:: sh

        papis merge --second "belief revision"

    By default, the second document is merged into the first. This flag reverses the
    order so that the first document is merged into the second.

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
from typing import TYPE_CHECKING

import click

import papis.cli
import papis.logging

if TYPE_CHECKING:
    from papis.document import Document

logger = papis.logging.get_logger(__name__)


def run(
        a: Document,
        b: Document,
        *,
        git: bool = False) -> None:
    """Merge the document *b* into *a*.

    The metadata of *b* is used to update *a* and its files are merged into the files of
    *a*. The notes of *b* replace the ``notes`` of *a*.
    """
    import shutil
    import tempfile

    from papis.document import describe
    from papis.exceptions import DocumentFolderNotFound

    a_folder = a.get_main_folder()
    if not a_folder:
        raise DocumentFolderNotFound(describe(a))

    if (b.get("files") or b.get("notes")) and not b.get_main_folder():
        raise DocumentFolderNotFound(describe(b))

    from papis.paths import make_unique_file

    file_names = a.get("files", []).copy()
    for f in b.get_files():
        logger.info("Copying file '%s' to '%s'.", os.path.basename(f), a_folder)
        notes_dst = make_unique_file(os.path.join(a_folder, os.path.basename(f)))
        shutil.copy(f, notes_dst)
        file_names.append(os.path.basename(notes_dst))

    if file_names:
        a["files"] = file_names

    b_notes = b.get_notes()
    if b_notes:
        b_notes = b_notes[0]
        logger.info("Copying notes '%s' to '%s'.", os.path.basename(b_notes), a_folder)

        handle, tmp_note = tempfile.mkstemp(dir=a_folder, prefix="papis-merge-note-")
        os.close(handle)
        try:
            shutil.copy(b_notes, tmp_note)

            if a.get("notes"):
                old_a_note = os.path.join(a_folder, a["notes"])
                logger.info("Replacing existing notes '%s'.", a["notes"])
                if os.path.exists(old_a_note):
                    os.remove(old_a_note)

            notes_dst = make_unique_file(
                os.path.join(a_folder, os.path.basename(b_notes))
            )
            os.replace(tmp_note, notes_dst)
        except Exception:
            if os.path.exists(tmp_note):
                os.remove(tmp_note)
            raise

        a["notes"] = os.path.basename(notes_dst)

    from papis.commands.update import run as update
    data = {k: v for k, v in b.items() if k not in {"files", "notes", "papis_id"}}
    update(a, data, git=git)


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

    from papis.document import Document, describe, sort, to_dict

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

    for d in (data_a, data_b):
        for k in ("files", "notes", "papis_id"):
            d.pop(k, None)

    if not batch:
        from papis.utils import update_doc_from_data_interactively
        logger.info("Select the metadata changes of B to apply to A.")
        update_doc_from_data_interactively(data_a, data_b, describe(b))

    from papis.tui.utils import confirm, select_range

    b_files = b.get_files()
    b_notes = notes[0] if (notes := b.get_notes()) else None
    notes: str | None = None
    if batch:
        conflicting = sorted(
            key
            for key in data_a.keys() & data_b.keys()
            if data_a[key] != data_b[key]
        )
        if conflicting:
            logger.warning(
                "Keeping the values of A for conflicting fields: %s",
                ", ".join(conflicting),
            )
        data_a.update({k: v for k, v in data_b.items() if k not in data_a})
        files = b_files
        notes = b_notes if not a.get("notes") else None
    else:
        if b_files:
            logger.info("Document B has files.")
        indices = select_range(b_files, "Files of B to keep", accept_none=True)
        files = [b_files[i] for i in indices]

        if b_notes:
            logger.info("Document B has notes.")
            if a.get("notes"):
                logger.warning(
                    "Document A has notes ('%s'), which will be replaced if B's notes"
                    " are added to it.", a["notes"])
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

    import shutil
    import tempfile

    with tempfile.TemporaryDirectory(prefix="papis-merge-tmp-") as scratch:
        scratch_doc = Document(folder=scratch, data=data_a)
        if files:
            file_names = []
            for f in files:
                # NOTE: the files of a document have unique names, so they only
                # clash once they are copied into the main document (see `run`)
                file_dst = os.path.join(scratch, os.path.basename(f))
                shutil.copy(f, file_dst)
                file_names.append(os.path.basename(file_dst))
            scratch_doc["files"] = file_names

        if notes:
            notes_dst = os.path.join(scratch, os.path.basename(notes))
            shutil.copy(notes, notes_dst)
            scratch_doc["notes"] = os.path.basename(notes_dst)

        run(a, scratch_doc, git=git)

    if keep_both:
        logger.info("Keeping both documents.")
    else:
        from papis.commands.rm import run as rm

        logger.info("Removing '%s'.", describe(b))
        rm(b, git=git)
