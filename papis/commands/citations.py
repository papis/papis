"""
See ../../doc/source/commands/citations.rst

papis citations --fetch-citations
"""
import click
from typing import Optional
import logging

import papis.cli
import papis.document
from papis.citations import (has_citations,
                             update_and_save_citations_from_database_from_doc,
                             fetch_and_save_citations)


@click.command("citations")
@click.help_option("--help", "-h")
@papis.cli.query_option()
@papis.cli.sort_option()
@click.option("-c", "--fetch-citations",
              default=False, is_flag=True,
              help="Fetch and save citations")
@click.option("-d", "--update-from-database",
              default=False, is_flag=True,
              help="Fetch and save citations")
@click.option("-f", "--force",
              default=False, is_flag=True,
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
        update_from_database: bool) -> None:
    """Check for common problems in documents"""

    logger = logging.getLogger("cli:citations")

    documents = papis.cli.handle_doc_folder_query_all_sort(query,
                                                           doc_folder,
                                                           sort_field,
                                                           sort_reverse,
                                                           _all)

    for document in documents:
        _has_citations_p = has_citations(document)
        if fetch_citations:
            if _has_citations_p and force or not _has_citations_p:
                logger.info("fetching citations for %s",
                            papis.document.describe(document))
                fetch_and_save_citations(document)
        if update_from_database:
            if _has_citations_p:
                logger.info("updating citations from library for %s",
                            papis.document.describe(document))
                update_and_save_citations_from_database_from_doc(document)
