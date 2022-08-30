import logging
from typing import List

import click

import papis.document


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
    logger = logging.getLogger("explore:json")
    logger.info("Reading in json file '%s'", jsonfile)

    import json
    docs = [papis.document.from_data(d) for d in json.load(open(jsonfile))]
    ctx.obj["documents"] += docs

    logger.info("%s documents found", len(docs))
