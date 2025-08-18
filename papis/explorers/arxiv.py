import click

import papis.cli
import papis.logging
from papis.explorers import as_explorer

logger = papis.logging.get_logger(__name__)


@as_explorer("arxiv")
@click.option("--query", "-q", default="", type=str)
@click.option("--author", "-a", default="", type=str)
@click.option("--title", "-t", default="", type=str)
@click.option("--abstract", default="", type=str)
@click.option("--comment", default="", type=str)
@click.option("--journal", default="", type=str)
@click.option("--report-number", default="", type=str)
@click.option("--category", default="", type=str)
@click.option("--id-list", default="", type=str)
@click.option("--page", default=0, type=int)
@click.option("--max", "-m", "max_results", default=20, type=int)
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
