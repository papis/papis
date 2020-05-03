import papis.document
import logging
import isbnlib
import isbnlib.registry
import click
# See https://github.com/xlcnd/isbnlib for details
from typing import Optional, Dict, Any, List

logger = logging.getLogger('papis:isbnlib')


def get_data(
        query: str = "",
        service: Optional[str] = None) -> List[Dict[str, Any]]:
    isbnlib_version = tuple(int(n) for n in isbnlib.__version__.split('.'))
    if service is None and isbnlib_version >= (3, 10, 0):
        service = "default"

    logger.debug('Trying to retrieve isbn')
    isbn = isbnlib.isbn_from_words(query)
    data = isbnlib.meta(isbn, service=service)

    results = []  # type: List[Dict[str, Any]]
    if data is not None:
        assert isinstance(data, dict)
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
@click.option(
    '--service',
    '-s',
    default='goob',
    type=click.Choice(list(isbnlib.registry.services.keys()))
)
def explorer(ctx: click.core.Context, query: str, service: str) -> None:
    """
    Look for documents using isbnlib

    Examples of its usage are

    papis explore isbn -q 'Albert einstein' pick cmd 'firefox {doc[url]}'

    """
    logger = logging.getLogger('explore:isbn')
    logger.info('Looking up...')
    data = get_data(
        query=query,
        service=service,
    )
    docs = [papis.document.from_data(data=d) for d in data]
    logger.info('{} documents found'.format(len(docs)))
    ctx.obj['documents'] += docs
