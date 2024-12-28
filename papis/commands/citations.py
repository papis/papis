"""
The ``citations`` command updates and creates the ``citations.yaml`` and
``cited.yaml`` files for every document.

Examples
^^^^^^^^

- Create the ``citations.yaml`` file for a document that you pick

    .. code:: sh

        papis citations --fetch-citations

- Create the ``citations.yaml`` file for all documents matching an author

    .. code:: sh

        papis citations --all --fetch-citations 'author:einstein'

- Overwrite the ``citations.yaml`` file with the ``--force`` flag for all
  papers matching a query

    .. code:: sh

        papis citations --force --fetch-citations 'author:einstein'

- Update the ``citations.yaml`` file with citations of documents existing in
  your library

    .. code:: sh

        papis citations --all --update-from-database 'author:einstein'

- Create the ``cited-by.yaml`` for all documents in your library (this might
  take a while)

    .. code:: sh

        papis citations --fetch-cited-by --all

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.citations:cli
    :prog: papis citations
"""

from typing import Optional, Tuple

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
@papis.cli.bool_flag("-c", "--fetch-citations",
                     help="Fetch and save citations from Crossref")
@papis.cli.bool_flag("-d", "--update-from-database",
                     help="Fetch and save citations from database")
@papis.cli.bool_flag("-b", "--fetch-cited-by",
                     help="Fetch and save cited-by from database")
@papis.cli.bool_flag("-f", "--force",
                     help="Force action")
@papis.cli.all_option()
@papis.cli.doc_folder_option()
def cli(query: str,
        doc_folder: Tuple[str, ...],
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
        has_citations_p = has_citations(document)
        has_cited_by_p = has_cited_by(document)
        if fetch_citations:
            if (has_citations_p and force) or not has_citations_p:
                logger.info("[%d/%d] Fetching citations for '%s'.",
                            i + 1, len(documents),
                            papis.document.describe(document))
                try:
                    fetch_and_save_citations(document)
                except ValueError as exc:
                    logger.error("Failed to fetch citations for document: '%s'",
                                 papis.document.describe(document), exc_info=exc)

        if update_from_database:
            if has_citations_p:
                logger.info("[%d/%d] Updating citations from library for '%s'.",
                            i + 1, len(documents),
                            papis.document.describe(document))
                update_and_save_citations_from_database_from_doc(document)
        if fetch_cited_by:
            if (has_cited_by_p and force) or not has_cited_by_p:
                logger.info(
                    "[%d/%d] Fetching cited-by references from library for '%s'",
                    i + 1, len(documents),
                    papis.document.describe(document))
                fetch_and_save_cited_by_from_database(document)
