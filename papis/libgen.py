import pylibgen
import click
import logging
import papis.document


@click.command('libgen')
@click.pass_context
@click.help_option('--help', '-h')
@click.option('--author', '-a', default=None)
@click.option('--title', '-t', default=None)
@click.option('--isbn', '-i', default=None)
def explorer(ctx, author, title, isbn):
    """
    Look for documents on library genesis

    Examples of its usage are

    papis explore libgen -a 'Albert einstein' export --yaml einstein.yaml

    """
    logger = logging.getLogger('explore:libgen')
    logger.info('Looking up...')
    lg = pylibgen.Library()
    ids = []

    if author:
        ids += lg.search(ascii(author), 'author')
    if isbn:
        ids += lg.search(ascii(isbn), 'isbn')
    if title:
        ids += lg.search(ascii(title), 'title')

    try:
        data = lg.lookup(ids)
    except:
        data = []

    docs = [papis.document.from_data(data=d.__dict__) for d in data]
    ctx.obj['documents'] += docs
    logger.info('{} documents found'.format(len(docs)))
