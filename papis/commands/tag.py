"""
This command allows users to add and remove tags to documents in their library.

Examples
^^^^^^^^

- To add a tag use the ``--add`` (or ``--append``/``-p``) option:

    .. code:: sh

        papis tag --add TAG1 --add TAG2 QUERY

  This will add TAG1 and TAG2 to a document matched by QUERY. You can repeat
  ``--add`` as many times as you need. The query is any query supported by Papis.
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

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.tag:cli
    :prog: papis tag

"""
from __future__ import annotations

from typing import TYPE_CHECKING

import click

import papis.cli
import papis.logging
from papis.commands.update import _OrderedCommand

if TYPE_CHECKING:
    from papis.strings import AnyString

logger = papis.logging.get_logger(__name__)


@click.command("tag", cls=_OrderedCommand)
@click.help_option("--help", "-h")
@papis.cli.git_option()
@papis.cli.bool_flag(
    "-d", "--drop",
    help="Drop all tags.",
    default=False,
)
@click.option(
    "-p", "--add", "--append", "to_append",
    help="Add a tag.",
    multiple=True,
    type=papis.cli.FormatPatternParamType(),
)
@click.option(
    "-r", "--remove", "to_remove",
    help="Remove a tag.",
    multiple=True,
    type=papis.cli.FormatPatternParamType(),
)
@click.option(
    "-n", "--rename", "to_rename",
    help="Rename a tag (<OLD-TAG NEW-TAG>).",
    multiple=True,
    type=(papis.cli.FormatPatternParamType(), papis.cli.FormatPatternParamType()),
)
@papis.cli.bool_flag(
    "-b",
    "--batch",
    help="Do not prompt, and skip documents containing errors."
)
@papis.cli.doc_folder_option()
@papis.cli.all_option()
@papis.cli.sort_option()
@papis.cli.query_argument()
@click.pass_context
def cli(
    ctx: click.Context,
    git: bool,
    drop: bool,
    to_append: list[AnyString],
    to_remove: list[AnyString],
    to_rename: list[tuple[AnyString, AnyString]],
    batch: bool,
    sort_field: str | None,
    sort_reverse: bool,
    query: str,
    doc_folder: tuple[str, ...],
    _all: bool,
) -> None:
    """
    Change a document's tags.
    """

    # retrieve documents
    documents = papis.cli.handle_doc_folder_query_all_sort(
        query, doc_folder, sort_field, sort_reverse, _all
    )
    if not documents:
        from papis.strings import no_documents_retrieved_message
        logger.warning(no_documents_retrieved_message)
        return

    # retrieve user provided operations
    from papis.commands.update import (
        _apply_operations,
        _process_command_line_operations,
    )

    operations = _process_command_line_operations(
        ctx.obj["param"],
        to_set=(),
        to_reset=(),
        to_drop=("tags",) if drop else (),
        to_append=(("tags", value) for value in to_append),
        to_remove=(("tags", value) for value in to_remove),
        to_rename=(("tags", from_value, to_value) for from_value, to_value in to_rename)
    )

    from papis.commands.update import ApplyStatus, run
    from papis.document import describe
    from papis.tui.utils import confirm as ask_confirm

    field_types: dict[str, type] = {"tags": list}

    ret = 0
    updated = 0
    for i, document in enumerate(documents):
        logger.info("[%d/%d] Applying metadata changes for document: %s.",
                    i + 1, len(documents), describe(document))

        tags = document.get("tags", [])
        if not isinstance(tags, list):
            logger.info("Document tags are not a list: %s. You can use "
                        "'papis doctor --checks field-type --fix' to automatically "
                        "convert all tags to lists.",
                        type(tags))
            logger.error("'papis tag' only supports list tags. Skipping...")

            ret = 1
            continue

        try:
            new_data, status = _apply_operations(
                document, operations,
                field_types=field_types)
        except Exception as exc:
            logger.error("Failed to apply metadata changes to document: %s.",
                         describe(document), exc_info=exc)
            ret = 1
            continue

        if ApplyStatus.Failed in status:
            ret = 1

        if ApplyStatus.Changed not in status:
            continue

        if ApplyStatus.Failed in status:
            if not batch and ask_confirm(
                "Encountered errors while updating document tags. Skip it?"
            ):
                continue

        try:
            run(document, data=new_data, git=git, auto_doctor=False, overwrite=True)
        except Exception as exc:
            logger.error("Failed to apply metadata changes to document: %s.",
                         describe(document), exc_info=exc)
            ret = 1
            continue

        updated += 1

    logger.info("Updated %d / %d documents.", updated, len(documents))
    ctx.exit(ret)
