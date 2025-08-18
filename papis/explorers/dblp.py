import click

import papis.cli
import papis.logging
from papis.explorers import as_explorer

logger = papis.logging.get_logger(__name__)


@as_explorer("dblp")
@click.option(
    "--query", "-q",
    help="General query.",
    default="")
@click.option(
    "--max", "-m", "max_results",
    help="Maximum number of results.",
    type=click.IntRange(1),
    default=30)
def cli(
        ctx: click.Context,
        query: str,
        max_results: int) -> None:
    """
    Look for documents on `dblp.org <https://dblp.org/>`__.

    For example, to look for a document with the author "Albert Einstein" and
    export it to a BibTeX file, you can call:

    .. code:: sh

        papis explore \\
            dblp -a 'Albert einstein' \\
            pick \\
            export --format bibtex --out lib.bib
    """
    if not query:
        logger.warning("No query provided.")
        return None

    logger.info("Looking up DBLP documents...")

    from papis.dblp import get_data

    data = get_data(query=query, max_results=max_results)
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj["documents"] += docs

    logger.info("Found %d documents.", len(docs))
