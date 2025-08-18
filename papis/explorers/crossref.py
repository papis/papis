import click

import papis.cli
import papis.logging
from papis.crossref import (
    CROSSREF_FILTER_NAMES,
    CROSSREF_ORDER_VALUES,
    CROSSREF_SORT_VALUES,
    get_data,
)
from papis.explorers import as_explorer

logger = papis.logging.get_logger(__name__)


@as_explorer("crossref")
@click.option(
    "-q", "--query",
    help="General query.",
    default="")
@click.option(
    "-a", "--author",
    help="Author of the query.",
    default="")
@click.option(
    "-t", "--title",
    help="Title of the query.",
    default="")
@click.option(
    "-m", "--max", "max_results",
    help="Maximum number of results.",
    default=20,
    show_default=True)
@click.option(
    "-f", "--filter", "filters",
    help="Filters to apply.",
    default=(),
    type=(click.Choice(list(CROSSREF_FILTER_NAMES)), str),
    multiple=True)
@click.option(
    "-o", "--order",
    help="Order of appearance according to sorting.",
    default="desc",
    type=click.Choice(list(CROSSREF_ORDER_VALUES)),
    show_default=True)
@click.option(
    "-s", "--sort",
    help="Sorting parameter.",
    default="score",
    type=click.Choice(list(CROSSREF_SORT_VALUES)),
    show_default=True)
def cli(ctx: click.Context,
        query: str,
        author: str,
        title: str,
        max_results: int,
        filters: list[tuple[str, str]],
        order: str,
        sort: str) -> None:
    """
    Look for documents on `Crossref <https://www.crossref.org/>`__.

    For example, to look for a document with the author "Albert Einstein" and
    export it to a BibTeX file, you can call:

    .. code:: sh

        papis explore \\
            crossref -a 'Albert einstein' \\
            pick \\
            export --format bibtex lib.bib
    """
    logger.info("Looking up Crossref documents...")

    data = get_data(
        query=query,
        author=author,
        title=title,
        max_results=max_results,
        filters=dict(filters),
        sort=sort,
        order=order)
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj["documents"] += docs

    logger.info("Found %s documents.", len(docs))
