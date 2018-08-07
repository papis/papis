"""

Cli
^^^
.. click:: papis.commands.explore:cli
    :prog: papis explore
    :show-nested:
"""
import papis.utils
import papis.commands
import papis.document
import papis.config
import papis.bibtex
import urllib.request
import tempfile
import papis.cli
import click
import logging
import papis.commands.add
import papis.commands.export
import papis.api


logger = logging.getLogger('explore')


# def do_add(doc, libgen=False, arxiv=False):
    # if libgen:
        # if not doc.has('doc_url'):
            # logger.error('No doc_url data retrieved')
            # return 1
        # logger.info('Downloading document')
        # doc_data = urllib.request.urlopen(
            # doc['doc_url']
        # ).read()
        # file_name = tempfile.mktemp()
        # with open(file_name, 'wb+') as fd:
            # fd.write(doc_data)
        # papis.commands.add.run([file_name], from_url=doc['doc_url'])
    # elif arxiv:
        # if not doc.has('url'):
            # logger.error('No url data retrieved')
            # return 1
        # papis.commands.add.run([], from_url=doc['doc_url'], no_document=True)


@click.group(invoke_without_command=False, chain=True)
@click.help_option('--help', '-h')
@click.pass_context
def cli(ctx):
    """
    Explore documents using a variety of resources
    """
    docs = []
    logger = logging.getLogger('explore:cli')
    ctx.obj = {'documents': []}


@cli.command('arxiv')
@click.pass_context
@click.help_option('--help', '-h')
@click.option('--query', '-q', default=None)
@click.option('--author', '-a', default=None)
@click.option('--title', '-t', default=None)
@click.option('--abstract', default=None)
@click.option('--comment', default=None)
@click.option('--journal', default=None)
@click.option('--report-number', default=None)
@click.option('--category', default=None)
@click.option('--id-list', default=None)
@click.option('--page', default=None)
@click.option('--max', '-m', default=20)
def arxiv(ctx, query, author, title, abstract, comment,
        journal, report_number, category, id_list, page, max):
    """
    Look for documents on ArXiV.org.

    Examples of its usage are

    papis explore arxiv -a 'Hummel' -m 100 arxiv -a 'Garnet Chan' pick
    """
    import papis.arxiv
    logger = logging.getLogger('explore:arxiv')
    logger.info('Looking up...')
    data = papis.arxiv.get_data(
        query=query,
        author=author,
        title=title,
        abstract=abstract,
        comment=comment,
        journal=journal,
        report_number=report_number,
        category=category,
        id_list=id_list,
        page=page or 0,
        max_results=max
    )
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj['documents'] += docs
    logger.info('{} documents found'.format(len(docs)))


@cli.command('libgen')
@click.pass_context
@click.help_option('--help', '-h')
@click.option('--author', '-a', default=None)
@click.option('--title', '-t', default=None)
@click.option('--isbn', '-i', default=None)
def libgen(ctx, author, title, isbn):
    """
    Look for documents on library genesis

    Examples of its usage are

    papis explore libgen -a 'Albert einstein' export --yaml einstein.yaml

    """
    from pylibgen import Library
    logger = logging.getLogger('explore:libgen')
    logger.info('Looking up...')
    lg = Library()
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


@cli.command('crossref')
@click.pass_context
@click.help_option('--help', '-h')
@click.option('--query', '-q', default=None)
@click.option('--author', '-a', default=None)
@click.option('--title', '-t', default=None)
@click.option('--max', '-m', default=20)
def crossref(ctx, query, author, title, max):
    """
    Look for documents on crossref.org.

    Examples of its usage are

    papis explore crossref -a 'Albert einstein' pick export --bibtex lib.bib

    """
    import papis.crossref
    logger = logging.getLogger('explore:crossref')
    logger.info('Looking up...')
    data = papis.crossref.get_data(
        query=query,
        author=author,
        title=title,
        max_results=max
    )
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj['documents'] += docs
    logger.info('{} documents found'.format(len(docs)))


@cli.command('isbnplus')
@click.pass_context
@click.help_option('--help', '-h')
@click.option('--query', '-q', default=None)
def isbnplus(ctx, query):
    """
    Look for documents on isbnplus.com

    Examples of its usage are

    papis explore isbnplus -q 'Albert einstein' pick cmd 'firefox {doc[url]}'

    """
    import papis.isbn
    logger = logging.getLogger('explore:isbnplus')
    logger.info('Looking up...')
    try:
        data = papis.isbn.get_data(query=query)
    except:
        data = []
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj['documents'] += docs
    logger.info('{} documents found'.format(len(docs)))


@cli.command('pick')
@click.pass_context
@click.help_option('--help', '-h')
def pick(ctx):
    """
    Pick from the retrieved documents

    Examples of its usage are

    papis explore bibtex lib.bib pick

    """
    docs = ctx.obj['documents']
    ctx.obj['documents'] = [papis.api.pick_doc(docs)]


@cli.command('bibtex')
@click.pass_context
@click.argument('bibfile', type=click.Path(exists=True))
@click.help_option('--help', '-h')
def bibtex(ctx, bibfile):
    """
    Import documents based on a bibtex file

    Examples of its usage are

    papis explore bibtex lib.bib pick

    """
    logger = logging.getLogger('explore:bibtex')
    logger.info('Reading in bibtex file {}'.format(bibfile))
    docs = [
        papis.document.from_data(d)
        for d in papis.bibtex.bibtex_to_dict(bibfile)
    ]
    ctx.obj['documents'] += docs
    logger.info('{} documents found'.format(len(docs)))


@cli.command('yaml')
@click.pass_context
@click.argument('yamlfile', type=click.Path(exists=True))
@click.help_option('--help', '-h')
def yaml(ctx, yamlfile):
    """
    Import documents based on a yaml file

    Examples of its usage are

    papis explore yaml lib.yaml pick

    """
    import yaml
    logger = logging.getLogger('explore:yaml')
    logger.info('Reading in yaml file {}'.format(yamlfile))
    docs = [
        papis.document.from_data(d) for d in yaml.load_all(open(yamlfile))
    ]
    ctx.obj['documents'] += docs
    logger.info('{} documents found'.format(len(docs)))


@cli.command('export')
@click.pass_context
@click.help_option('--help', '-h')
@click.option(
    "--bibtex",
    help="Export list of documents retrieved to a bibtex file",
    type=click.Path(),
    default=None
)
@click.option(
    "--yaml",
    help="Export list of documents retrieved to a yaml file",
    type=click.Path(),
    default=None
)
def export(ctx, bibtex, yaml):
    """
    Import documents based on a yaml file

    Examples of its usage are

    papis explore crossref -m 200 -a 'Schrodinger' export --yaml lib.yaml

    """
    logger = logging.getLogger('explore:yaml')
    docs = ctx.obj['documents']

    if yaml:
        with open(yaml, 'a+') as fd:
            logger.info(
                "Writing {} documents' yaml into {}".format(
                    len(docs),
                    yaml
                )
            )
            yamldata = papis.commands.export.run(docs, yaml=True)
            fd.write(yamldata)

    if bibtex:
        with open(bibtex, 'a+') as fd:
            logger.info(
                "Writing {} documents' bibtex into {}".format(
                    len(docs),
                    yaml
                )
            )
            bibtexdata = papis.commands.export.run(docs, bibtex=True)
            fd.write(bibtexdata)


@cli.command('cmd')
@click.pass_context
@click.help_option('--help', '-h')
@click.argument('command', type=str)
def export(ctx, command):
    """
    Import documents based on a yaml file

    Examples of its usage are:

    Look for 200 Schroedinger papers, pick one, and add it via papis-scihub

    papis explore crossref -m 200 -a 'Schrodinger' pick cmd 'papis scihub {doc[doi]}'

    """
    from subprocess import call
    logger = logging.getLogger('explore:cmd')
    docs = ctx.obj['documents']
    for doc in docs:
        fcommand = papis.utils.format_doc(command, doc)
        logger.info('Calling "%s"' % fcommand)
        call(fcommand.split(" "))
