import click

import papis.cli
import papis.logging
from papis.explorers import as_explorer

logger = papis.logging.get_logger(__name__)


@as_explorer("citations")
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@papis.cli.bool_flag(
    "-b",
    "--cited-by",
    help="Explore the cited-by citations.")
@papis.cli.all_option()
def cli(ctx: click.Context,
        query: str,
        doc_folder: tuple[str, ...],
        cited_by: bool,
        _all: bool) -> None:
    """
    Query the citations for a paper.

    For example, to go through the citations of a paper and export it in a
    YAML file, you can call:

    .. code:: sh

        papis explore citations 'einstein' export --format yaml --out 'einstein.yaml'
    """
    if not (query or doc_folder):
        logger.warning("No query or document folder provided.")
        return None

    from papis.api import get_documents_in_lib, pick_doc
    from papis.document import describe, from_folder

    if doc_folder is not None:
        documents = [from_folder(d) for d in doc_folder]
    else:
        from papis.config import get_lib_name

        documents = get_documents_in_lib(get_lib_name(), search=query)

    if not _all:
        documents = pick_doc(documents)  # type: ignore[assignment]

    if not documents:
        from papis.strings import no_documents_retrieved_message

        logger.warning(no_documents_retrieved_message)
        return

    from papis.citations import get_citations, get_cited_by

    for document in documents:
        logger.debug("Exploring document '%s'.", describe(document))

        citations = get_cited_by(document) if cited_by else get_citations(document)
        logger.debug("Found %d citations.", len(citations))

        ctx.obj["documents"].extend(citations)
