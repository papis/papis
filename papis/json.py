from typing import List

import click

import papis.document
import papis.logging

logger = papis.logging.get_logger(__name__)


def exporter(documents: List[papis.document.Document]) -> str:
    import json
    return json.dumps([papis.document.to_dict(doc) for doc in documents])


@click.command("json")
@click.pass_context
@click.argument("jsonfile", type=click.Path(exists=True))
@click.help_option("--help", "-h")
def explorer(ctx: click.Context, jsonfile: str) -> None:
    """
    Import documents from a json file

    Examples of its usage are

    papis explore json lib.json pick

    """
    logger.info("Reading JSON file '%s'...", jsonfile)

    import json

    with open(jsonfile) as f:
        docs = [papis.document.from_data(d) for d in json.load(f)]
        ctx.obj["documents"] += docs

    logger.info("Found %s documents.", len(docs))
