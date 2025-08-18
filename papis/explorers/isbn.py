import click

import papis.cli
import papis.logging
from papis.explorers import as_explorer
from papis.isbn import ISBN_SERVICE_NAMES, get_data

logger = papis.logging.get_logger(__name__)


@as_explorer("isbn")
@click.option("--query", "-q", default=None)
@click.option("--service", "-s",
              default=ISBN_SERVICE_NAMES[0],
              type=click.Choice(ISBN_SERVICE_NAMES))
def cli(ctx: click.core.Context, query: str, service: str) -> None:
    """
    Look for documents using `isbnlib <https://isbnlib.readthedocs.io/>`__.

    For example, to look for a document with the author "Albert Einstein" and
    open it with Firefox, you can call:

    .. code:: sh

        papis explore \\
            isbn -q 'Albert einstein' \\
            pick \\
            cmd 'firefox {doc[url]}'
    """
    if not query:
        logger.warning("No query provided.")
        return None

    logger.info("Looking up ISBN documents...")

    data = get_data(query=query, service=service)
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj["documents"] += docs

    logger.info("Found %d documents.", len(docs))
