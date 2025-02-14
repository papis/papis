"""
This command allows users to add and remove tags to documents in their library.

Examples
^^^^^^^^

- To add a tag use the ``--add`` (or ``--append``/``-p``) option:

    .. code:: sh

        papis tag --add TAG1 --add TAG2 QUERY

  This will add TAG1 and TAG2 to a document matched by QUERY. You can repeat
  ``--add`` as many times as you need. The query is any query supported by papis.
  If the query matches more than one document, Papis' picker will be started to
  let you pick the document from those matched (just as with Papis' other
  commands).

  Tags are only added if they do not already exist, which is to say that the
  same tag cannot exist more than once in a given document.

- To remove a tag use the ``--remove`` (or ``-r``) option:

    .. code:: sh

        papis tag --remove TAG1 QUERY

  This removes TAG1 from the document. If it didn't exist before, nothing
  happens. You can use ``--remove`` as many times as you like to remove multiple
  tags.

- Use ``--drop`` (or ``-d``) to remove all tags:

    .. code:: sh

        papis tag --drop --add TAG1 QUERY

  This removes all tags from the document and then adds TAG1. You can of course
  also use ``--drop`` by itself to simply remove all tags without adding new
  ones.

- Use ``--all`` (or ``-a``) with any of the other options to apply the tagging
  operation to all matching documents:

    .. code:: sh

        papis tag --all --add TAG1 QUERY

  This adds TAG1 to all documents matching the QUERY rather than opening the
  picker to let you choose one.

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.tag:cli
    :prog: papis tag

"""

from typing import List, Optional, Tuple, Any, Dict

import click

import papis.cli
import papis.commands
import papis.importer
import papis.strings

logger = papis.logging.get_logger(__name__)


@click.command("tag")
@click.help_option("--help", "-h")
@papis.cli.git_option()
@papis.cli.bool_flag(
    "-d",
    "--drop",
    help="Drop all tags",
    default=False,
)
@click.option(
    "-p",
    "--add",
    "--append",
    "to_add",
    help="Add a tag",
    multiple=True,
    type=str,
)
@click.option(
    "-r",
    "--remove",
    "to_remove",
    help="Remove a tag",
    multiple=True,
    type=str,
)
@click.option(
    "-n",
    "--rename",
    "to_rename",
    help="Rename a tag (<OLD-TAG NEW-TAG>)",
    multiple=True,
    type=(str, str),
)
@papis.cli.doc_folder_option()
@papis.cli.all_option()
@papis.cli.sort_option()
@papis.cli.query_argument()
def cli(
    git: bool,
    drop: bool,
    to_add: List[str],
    to_remove: List[str],
    to_rename: List[Tuple[str, str]],
    sort_field: Optional[str],
    sort_reverse: bool,
    query: str,
    doc_folder: Tuple[str, ...],
    _all: bool,
) -> None:
    """
    Change a document's tags.
    """

    # if do_tag:
    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder, sort_field, sort_reverse, _all
    )

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    from papis.commands.update import run_append, run_remove, run_drop, run_rename, run

    key_types: Dict[str, type] = {"tags": list}

    success = True
    processed_documents: List[Any] = []
    for document in documents:
        tags = document.get("tags", [])
        if not isinstance(tags, list):
            processed_documents.clear()
            logger.error(
                "The document with papis_id '%s' contains tags that aren't "
                "defined as a list of items. As `papis tag` only supports "
                "lists, tagging has been aborted and no documents have been "
                "changed. You can use `papis doctor --checks key-type --fix` to "
                "convert all your tags to use lists.",
                document["papis_id"],
            )
            break

        ctx = papis.importer.Context()

        ctx.data.update(document)
        if drop and success:
            run_drop(ctx.data, ["tags"])

        if to_add and success:
            to_add_tuples = [("tags", tag) for tag in to_add]
            success = run_append(ctx.data, to_add_tuples, key_types, False)

        if to_remove and success:
            to_remove_tuples = [("tags", tag) for tag in to_remove]
            success = run_remove(ctx.data, to_remove_tuples, False)

        if to_rename:
            to_rename_tuples = [
                ("tags", old_tag, new_tag) for old_tag, new_tag in to_rename
            ]
            success = run_rename(ctx.data, to_rename_tuples, False)

        if success:
            processed_documents.append((document, ctx.data))

        if not success:
            processed_documents.clear()
            logger.error(
                "Papis has encountered an unexpected error while processing "
                "document '%s'. Tagging has been aborted and no documents have "
                "been changed. Please report this bug at "
                "https://github.com/papis/papis.",
                document["papis_id"],
            )
            break

    for document, data in processed_documents:
        run(document, data=data, git=git, auto_doctor=False)

    logger.info("Updated tags in %d documents", len(processed_documents))
