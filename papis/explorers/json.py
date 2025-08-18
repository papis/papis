import click

import papis.cli
import papis.logging
from papis.explorers import as_explorer

logger = papis.logging.get_logger(__name__)


@as_explorer("json")
@click.argument("jsonfile", type=click.Path(exists=True))
def cli(ctx: click.Context, jsonfile: str) -> None:
    """
    Import documents from a JSON file.

    For example, you can call:

    .. code:: sh

        papis explore json 'lib.json' pick
    """
    logger.info("Reading JSON file '%s'...", jsonfile)

    import json

    with open(jsonfile, encoding="utf-8") as f:
        docs = [papis.document.from_data(d) for d in json.load(f)]
        ctx.obj["documents"] += docs

    logger.info("Found %s documents.", len(docs))
