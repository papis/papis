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


logger = logging.getLogger('explore')


def parse_search(query):
    import papis.docmatcher
    key_vals = papis.docmatcher.parse_query(query)
    result = {'query': ""}
    logger.debug('Parsed set %s' % key_vals)
    for pair in key_vals:
        if len(pair) == 3:
            key = pair[0]
            val = pair[2]
            result[key] = val
        else:
            val = pair[0]
            result['query'] += ' ' + val
    return result


def do_add(doc, libgen=False, arxiv=False):
    if libgen:
        if not doc.has('doc_url'):
            logger.error('No doc_url data retrieved')
            return 1
        logger.info('Downloading document')
        doc_data = urllib.request.urlopen(
            doc['doc_url']
        ).read()
        file_name = tempfile.mktemp()
        with open(file_name, 'wb+') as fd:
            fd.write(doc_data)
        papis.commands.add.run([file_name], from_url=doc['doc_url'])
    elif arxiv:
        if not doc.has('url'):
            error('No url data retrieved')
            return 1
        papis.commands.add.run([], from_url=doc['doc_url'], no_document=True)


def explore_libgen(query):
    from pylibgen import Library
    parsed = parse_search(query)
    lg = Library()
    ids = []
    for key in ['title', 'author', 'isbn']:
        if parsed.get(key):
            ids += lg.search(ascii(parsed.get(key)), key)
    if len(ids) == 0:
        ids = lg.search(ascii(parsed.get('query')), 'title')
    if len(ids):
        data = lg.lookup(ids)
    else:
        logger.error("No documents found")
        return None
    doc = papis.cli.pick(
        [papis.document.Document(data=d) for d in data]
    )
    if doc:
        doc['doc_url'] = lg.get_download_url(doc['md5'])
    return doc


def explore_crossref(search, max_results):
    import papis.crossref
    parsed = parse_search(query)
    data = papis.crossref.get_data(
        query=parsed.get('query'),
        author=parsed.get('author'),
        title=parsed.get('title'),
        year=parsed.get('year'),
        max_results=max_results
    )
    documents = [papis.document.Document(data=d) for d in data]
    doc = papis.cli.pick(
        documents
    )
    return doc


def explore_isbnplus(query):
    import papis.isbn
    data = papis.isbn.get_data(query=query)
    doc = papis.cli.pick(
        [papis.document.Document(data=d) for d in data]
    )
    return doc


def explore_arxiv(query, max_results):
    import papis.arxiv
    parsed = parse_search(query)
    data = papis.arxiv.get_data(
        query=parsed.get('query'),
        author=parsed.get('author'),
        title=parsed.get('title'),
        abstract=parsed.get('abstract'),
        comment=parsed.get('comment'),
        journal=parsed.get('journal'),
        report_number=parsed.get('report_number'),
        category=parsed.get('category'),
        id_list=parsed.get('id_list'),
        page=parsed.get('page') or 0,
        max_results=max_results
    )
    doc = papis.cli.pick(
        [papis.document.Document(data=d) for d in data]
    )
    return doc


@click.command()
@click.help_option('--help', '-h')
@papis.cli.query_option()
@click.option(
    "--isbnplus",
    help="Search through isbnplus.org",
    default=False,
    is_flag=True
)
@click.option(
    "--arxiv",
    help="Search on the arxiv",
    default=False,
    is_flag=True
)
@click.option(
    "--libgen",
    help="Search on library genesis",
    default=False,
    is_flag=True
)
@click.option(
    "--crossref",
    help="Search on library genesis",
    default=False,
    is_flag=True
)
@click.option(
    "--add",
    help="Add document selected",
    default=False,
    is_flag=True
)
@click.option(
    "--max",
    help="Maximum number of items",
    default=30,
    type=int
)
@click.option(
    "--cmd",
    help="Issue a command on the retrieved document "
         "using papis format",
    default=None
)
def cli(
        query,
        isbnplus,
        arxiv,
        libgen,
        crossref,
        add,
        max,
        cmd
    ):
    """Explore on the internet"""
    doc = None
    if arxiv:
        doc = explore_arxiv(query, max)
    elif isbnplus:
        doc = explore_isbnplus(query)
    elif crossref:
        doc = explore_crossref(query, max)
    elif libgen:
        doc = explore_libgen(query)
    else:
        arxiv = True
        doc = explore_arxiv(query, max)

    if doc:
        print(papis.document.dump(doc))
        if add:
            do_add(doc, libgen, arxiv)
        elif cmd is not None:
            from subprocess import call
            command = papis.utils.format_doc(cmd, doc)
            logger.debug('Calling "%s"' % command)
            call(command.split(" "))
