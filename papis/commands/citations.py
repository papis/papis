"""
See ../../doc/source/commands/citations.rst

papis citations --fetch-citations
"""
from typing import Optional

import click

import papis.cli
import papis.document
import papis.logging
from papis.citations import (has_citations,
                             has_cited_by,
                             update_and_save_citations_from_database_from_doc,
                             fetch_and_save_citations,
                             fetch_and_save_cited_by_from_database)

logger = papis.logging.get_logger(__name__)


@click.command("citations")
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@papis.cli.sort_option()
@click.option("-c",
              "--fetch-citations",
              default=False,
              is_flag=True,
              help="Fetch and save citations")
@click.option("-d",
              "--update-from-database",
              default=False,
              is_flag=True,
              help="Fetch and save citations")
@click.option("-f",
              "--force",
              default=False,
              is_flag=True,
              help="Force action")
@click.option("-b",
              "--fetch-cited-by",
              default=False,
              is_flag=True,
              help="Force action")
@papis.cli.all_option()
@papis.cli.doc_folder_option()
def cli(query: str,
        doc_folder: str,
        sort_field: Optional[str],
        sort_reverse: bool,
        _all: bool,
        force: bool,
        fetch_citations: bool,
        fetch_cited_by: bool,
        update_from_database: bool) -> None:
    """Handle document citations"""
    documents = papis.cli.handle_doc_folder_query_all_sort(query,
                                                           doc_folder,
                                                           sort_field,
                                                           sort_reverse,
                                                           _all)

    for i, document in enumerate(documents):
        _has_citations_p = has_citations(document)
        _has_cited_by_p = has_cited_by(document)
        if fetch_citations:
            if _has_citations_p and force or not _has_citations_p:
                logger.info("[%d/%d] Fetching citations for '%s'.",
                            i + 1, len(documents),
                            papis.document.describe(document))
                fetch_and_save_citations(document)
        if update_from_database:
            if _has_citations_p:
                logger.info("[%d/%d] Updating citations from library for '%s'.",
                            i + 1, len(documents),
                            papis.document.describe(document))
                update_and_save_citations_from_database_from_doc(document)
        if fetch_cited_by:
            if _has_cited_by_p and force or not _has_cited_by_p:
                logger.info(
                    "[%d/%d] Fetching cited-by references from library for '%s'",
                    i + 1, len(documents),
                    papis.document.describe(document))
                fetch_and_save_cited_by_from_database(document)
