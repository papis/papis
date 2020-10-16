import papis.document
import logging
import isbnlib
import click
# See https://github.com/xlcnd/isbnlib for details
from typing import Dict, Any, List

logger = logging.getLogger('papis:isbnlib')


def get_data(query: str = "",
             service: str = 'openl') -> List[Dict[str, Any]]:
    global logger
    results = []  # type: List[Dict[str, Any]]
    logger.debug('Trying to retrieve isbn')
    isbn = isbnlib.isbn_from_words(query)
    data = isbnlib.meta(isbn, service=service)
    if data is None:
        return results
    else:
        logger.debug('Trying to retrieve isbn')
        assert(isinstance(data, dict))
        results.append(data_to_papis(data))
        return results


def data_to_papis(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert data from isbnlib into papis formated data

    :param data: Dictionary with data
    :type  data: dict
    :returns: Dictionary with papis keynames

    """
    data = {k.lower(): data[k] for k in data}
    return data


@click.command('isbn')
@click.pass_context
@click.help_option('--help', '-h')
@click.option('--query', '-q', default=None)
@click.option('--service', '-s',
              default='goob',
              type=click.Choice(['wcat', 'goob', 'openl']))
def explorer(ctx: click.core.Context, query: str, service: str) -> None:
    """
    Look for documents using isbnlib

    Examples of its usage are

    papis explore isbn -q 'Albert einstein' pick cmd 'firefox {doc[url]}'

    """
    logger = logging.getLogger('explore:isbn')
    logger.info('Looking up...')
    data = get_data(query=query, service=service)
    docs = [papis.document.from_data(data=d) for d in data]
    logger.info('{} documents found'.format(len(docs)))
    ctx.obj['documents'] += docs
