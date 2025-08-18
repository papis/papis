import click

import papis.cli
import papis.logging
from papis.explorers import as_explorer

logger = papis.logging.get_logger(__name__)


@as_explorer("arxiv")
@click.option(
    "-q", "--query",
    default="")
@click.option(
    "-a", "--author",
    default="")
@click.option(
    "-t", "--title",
    default="")
@click.option("--abstract", default="")
@click.option("--comment", default="")
@click.option("--journal", default="")
@click.option("--report-number", default="")
@click.option("--category", default="")
@click.option("--id-list", default="")
@click.option("--page", default=0, type=click.IntRange(0))
@click.option("--max", "-m", "max_results", default=20, type=click.IntRange(1))
def cli(ctx: click.Context,
        query: str,
        author: str,
        title: str,
        abstract: str,
        comment: str,
        journal: str,
        report_number: str,
        category: str,
        id_list: str,
        page: int,
        max_results: int) -> None:
    """
    Look for documents on `arXiv.org <https://arxiv.org/>`__.

    For example, to search for documents with the authors "Hummel" and
    "Garnet Chan" (limited to a maximum of 100 articles), use:

    .. code:: sh

        papis explore arxiv -a 'Hummel' -m 100 arxiv -a 'Garnet Chan' pick

    If you want to search for the exact author name 'John Smith', you should
    enclose it in extra quotes, as in the example below:

    .. code:: sh

        papis explore arxiv -a '"John Smith"' pick

    """
    logger.info("Looking up arXiv documents...")

    from papis.arxiv import get_data

    data = get_data(
        query=query,
        author=author,
        title=title,
        abstract=abstract,
        comment=comment,
        journal=journal,
        report_number=report_number,
        category=category,
        id_list=id_list,
        page=page or 0,
        max_results=max_results)
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj["documents"] += docs

    logger.info("Found %s documents.", len(docs))
