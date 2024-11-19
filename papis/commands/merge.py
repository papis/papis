"""
Merge two documents that might be potentially duplicated.

If your Papis picker does not support selecting two items, then
pass the ``--pick`` flag to pick twice from the documents.

Examples
^^^^^^^^

-   Pick the duplicate documents:

    .. code:: sh

        papis merge "prediction and subs"

        /papers/de8d6373a8cef74b5245124ddb288d45-dejong-gerald
        /papers/0e378c330dba4a4483660388183aa648-dejong-gerald

    With the default picker and config, you can pick the two offending documents
    with ``CTRL+T`` The selected entries will have a ``#`` in the beginning of
    the document title.

    Papis will show the difference between the files and let you select which
    ones you want to keep:

    .. code:: diff

        - collections: ['t3']
        + collections: ['t3', 't3a2']

    The lines are prefixed by an indication of what will happen on accepting the
    change. Papis will remove lines prefixed with a minus sign and add those
    with a plus sign.

-   Merge the documents that match the query "prediction and subs" and commit
    the changes to git:

    .. code:: sh

        papis merge --git "prediction and subs"

-   Choose which documents to keep:

    .. code:: sh

        papis merge --keep "belief revision"

    After deciding which changes to apply, Papis will prompt for files that
    should be moved to the resulting location. The files can be chosen entering
    the numbers that precede the documents.


Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.merge:cli
    :prog: papis merge
"""

import os
from typing import Optional, List, Dict, Any

import click

import papis
import papis.api
import papis.pick
import papis.utils
import papis.config
import papis.cli
import papis.database
import papis.document
import papis.format
import papis.strings
import papis.commands.rm
import papis.commands.update
import papis.logging

logger = papis.logging.get_logger(__name__)


def run(keep: papis.document.Document,
        erase: papis.document.Document,
        data: Dict[str, Any],
        files: List[str],
        keep_both: bool,
        git: bool = False) -> None:

    files_to_move = set(files) - set(keep.get_files())
    for f in files_to_move:
        to_folder = keep.get_main_folder()
        if to_folder:
            import shutil
            logger.info("Moving '%s' to '%s'.", f, to_folder)
            shutil.copy(f, to_folder)
            keep.get("files", []).extend([os.path.basename(f)])
    papis.commands.update.run(keep, data, git=git)

    if not keep_both:
        logger.info("Removing '%s'.", papis.document.describe(erase))
        papis.commands.rm.run(erase, git=git)
    else:
        logger.info("Keeping both documents.")


@click.command("merge")
@click.help_option("-h", "--help")
@papis.cli.query_argument()
@papis.cli.sort_option()
@papis.cli.bool_flag(
    "-s", "--second",
    help="Keep the second document after merge and erase the first, "
         "the default is keep the first")
@papis.cli.bool_flag(
    "-p", "--pick",
    help="If your picker does not support picking two documents"
         " at once, call twice the picker to get two documents")
@papis.cli.bool_flag(
    "-k", "--keep", "keep_both",
    help="Do not erase any document")
@click.option("-o",
              "--out",
              help="Create the resulting document in this path",
              default=None)
@papis.cli.git_option(help="Merge in git")
def cli(query: str,
        sort_field: Optional[str],
        out: Optional[str],
        second: bool,
        git: bool,
        keep_both: bool,
        sort_reverse: bool,
        pick: bool) -> None:
    """Merge two documents from a given library"""
    documents = papis.database.get().query(query)

    if sort_field:
        documents = papis.document.sort(documents, sort_field, sort_reverse)

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    documents = papis.pick.pick_doc(documents)

    if pick:
        other_documents = papis.pick.pick_doc(documents)
        documents += other_documents

    if len(documents) != 2:
        logger.error(
            "You have to pick exactly two documents (picked %d)!",
            len(documents))
        return

    a = documents[0]
    data_a = papis.document.to_dict(a)
    b = documents[1]
    data_b = papis.document.to_dict(b)

    to_pop = ["files"]
    for d in (data_a, data_b):
        for key in to_pop:
            if key in d:
                d.pop(key)

    papis.utils.update_doc_from_data_interactively(data_a,
                                                   data_b,
                                                   papis.document.describe(b))

    files: List[str] = []
    for doc in documents:
        indices = papis.tui.utils.select_range(
            doc.get_files(),
            "Documents from A to keep",
            accept_none=True,
            bottom_toolbar=papis.document.describe(a))
        files += [doc.get_files()[i] for i in indices]

    if not papis.tui.utils.confirm("Are you sure you want to merge?"):
        return

    keep = b if second else a
    erase = a if second else b

    if out is not None:
        import shutil

        os.makedirs(out, exist_ok=True)
        keep = papis.document.from_folder(out)
        keep["files"] = []
        for f in files:
            shutil.copy(f, out)
            keep["files"] += [os.path.basename(f)]
        keep.update(data_a)
        keep.save()
        logger.info("Saving the new document in '%s'.", out)
        return

    run(keep, erase, data_a, files, keep_both, git)
