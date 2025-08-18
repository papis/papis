import click

import papis.cli
import papis.logging
from papis.explorers import as_explorer

logger = papis.logging.get_logger(__name__)


@as_explorer("lib")
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@click.option(
    "-l",
    "--library",
    default=None,
    help="Papis library to explore.",
)
def cli(ctx: click.Context,
        query: str,
        doc_folder: tuple[str, ...],
        library: str | None) -> None:
    """
    Query for documents in a local Papis library.

    For example, to query all the documents containing "einstein" in the "books"
    library, you can call:

    .. code:: sh

        papis explore lib -l books 'einstein' pick
    """

    from papis.document import from_folder

    if doc_folder:
        ctx.obj["documents"] += [from_folder(d) for d in doc_folder]

    from papis.database import get

    db = get(library_name=library)
    docs = db.query(query)
    logger.info("Found %d documents.", len(docs))

    ctx.obj["documents"] += docs
    assert isinstance(ctx.obj["documents"], list)
