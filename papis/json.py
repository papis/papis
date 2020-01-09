import click
import json
import logging
from typing import List

import papis.document


def exporter(documents: List[papis.document.Document]) -> str:
    return json.dumps([papis.document.to_dict(doc) for doc in documents])


@click.command('json')
@click.pass_context
@click.argument('jsonfile', type=click.Path(exists=True))
@click.help_option('--help', '-h')
def explorer(ctx: click.Context, jsonfile: str) -> None:
    """
    Import documents from a json file

    Examples of its usage are

    papis explore json lib.json pick

    """
    logger = logging.getLogger('explore:json')
    logger.info('Reading in json file {}'.format(jsonfile))
    docs = [papis.document.from_data(d) for d in json.load(open(jsonfile))]
    ctx.obj['documents'] += docs
    logger.info('{} documents found'.format(len(docs)))
