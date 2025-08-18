import click

import papis.cli
import papis.logging
from papis.explorers import as_explorer

logger = papis.logging.get_logger(__name__)


@as_explorer("bibtex")
@click.argument("bibfile", type=click.Path(exists=True))
def cli(ctx: click.Context, bibfile: str) -> None:
    """Import documents from a BibTeX file.

    This explorer can be used as:

    .. code:: sh

        papis explore bibtex 'lib.bib' pick
    """
    logger.info("Reading BibTeX file '%s'...", bibfile)

    from papis.bibtex import bibtex_to_dict

    docs = [
        papis.document.from_data(d)
        for d in bibtex_to_dict(bibfile)]
    ctx.obj["documents"] += docs

    logger.info("Found %d documents.", len(docs))
