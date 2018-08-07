"""

Cli
^^^
.. click:: papis.commands.explore:cli
    :prog: papis explore
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
            logger.error('No url data retrieved')
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
    docs = [papis.document.from_data(data=d) for d in data]
    for doc in docs:
        doc['doc_url'] = lg.get_download_url(doc['md5'])
    return docs


def explore_crossref(query, max_results):
    import papis.crossref
    parsed = parse_search(query)
    data = papis.crossref.get_data(
        query=parsed.get('query'),
        author=parsed.get('author'),
        title=parsed.get('title'),
        max_results=max_results
    )
    return [papis.document.from_data(data=d) for d in data]


def explore_isbnplus(query):
    import papis.isbn
    data = papis.isbn.get_data(query=query)
    return [papis.document.from_data(data=d) for d in data]


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
    return [papis.document.from_data(data=d) for d in data]


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
    help="Maximum number of items to be retrieved",
    default=30,
    type=int
)
@click.option(
    "--cmd",
    help="Issue a command on the retrieved document "
         "using papis format (e.g. --cmd 'papis scihub {doc[doi]}')",
    default=None
)
@click.option(
    "--from-bibtex",
    help="Import document list a bibtex file",
    type=click.Path(exists=True),
    default=None
)
@click.option(
    "--export-bibtex",
    help="Export list of documents retrieved to a bibtex file",
    type=click.Path(),
    default=None
)
@click.option(
    "--from-yaml",
    help="Import document list a yaml file",
    type=click.Path(exists=True),
    default=None
)
@click.option(
    "--export-yaml",
    help="Export list of documents retrieved to a yaml file",
    type=click.Path(),
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
        cmd,
        from_bibtex,
        export_bibtex,
        from_yaml,
        export_yaml
        ):
    """Explore on the internet"""
    docs = []
    logger = logging.getLogger('explore:cli')

    if arxiv:
        docs = explore_arxiv(query, max)
    elif isbnplus:
        docs = explore_isbnplus(query)
    elif crossref:
        docs = explore_crossref(query, max)
    elif libgen:
        docs = explore_libgen(query)
    elif from_bibtex:
        logger.info('Reading in bibtex file {}'.format(from_yaml))
        docs = [
            papis.document.from_data(d)
            for d in papis.bibtex.bibtex_to_dict(from_bibtex)
        ]
    elif from_yaml:
        import yaml
        logger.info('Reading in yaml file {}'.format(from_yaml))
        docs = [
            papis.document.from_data(d) for d in yaml.load_all(open(from_yaml))
        ]
    else:
        arxiv = True
        docs = explore_arxiv(query, max)

    logger.info('{} documents found'.format(len(docs)))
    if len(docs) == 0:
        return 0

    if export_yaml:
        with open(export_yaml, 'a+') as fd:
            logger.error("Writing documents' yaml into {}".format(export_yaml))
            yamldata = papis.commands.export.run(docs, yaml=True)
            fd.write(yamldata)

    if export_bibtex:
        with open(export_bibtex, 'a+') as fd:
            logger.error(
                "Writing documents' bibtex into {}".format(export_bibtex)
            )
            bibtexdata = papis.commands.export.run(docs, bibtex=True)
            fd.write(bibtexdata)

    doc = papis.api.pick_doc(docs)

    if doc:
        click.echo(papis.document.dump(doc))
        if add:
            do_add(doc, libgen, arxiv)
        elif cmd is not None:
            from subprocess import call
            command = papis.utils.format_doc(cmd, doc)
            logger.debug('Calling "%s"' % command)
            call(command.split(" "))
