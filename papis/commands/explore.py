"""
This command is in an experimental stage but it might be useful for many
people.

Imagine you want to search for some papers online, but you don't want to
go into a browser and look for it. Explore gives you way to do this,
using several services available online, more should be coming on the way.

An excellent such resource is `crossref <https://crossref.org/>`_,
which you can use by using the subcommand crossref:

::

    papis explore crossref --author 'Freeman Dyson'

If you issue this command, you will see some text but basically nothing
will happen. This is because ``explore`` is conceived in such a way
as to concatenate commands, doing a simple

::

    papis explore crossref -h

will tell you which commands are available.
Let us suppose that you want to look for some documents on crossref,
say some papers of Schroedinger, and you want to store them into a bibtex
file called ``lib.bib``, then you could concatenate the commands
``crossref`` and ``export --bibtex`` as such

::

    papis explore crossref -a 'Schrodinger' export --bibtex lib.bib

This will store everything that you got from crossref in the file ``lib.bib``
and store in bibtex format. ``explore`` is much more flexible than that,
you can also pick just one document to store, for instance let's assume that
you don't want to store all retrieved documents but only one that you pick,
the ``pick`` command will take care of it

::

    papis explore crossref -a 'Schrodinger' pick export --bibtex lib.bib

notice how the ``pick`` command is situated before the ``export``.
More generally you could write something like

::

    papis explore \\
        crossref -a Schroedinger \\
        crossref -a Einstein \\
        arxiv -a 'Felix Hummel' \\
        export --yaml docs.yaml \\
        pick  \\
        export --bibtex specially-picked-document.bib

The upper command will look in crossref for documents authored by Schrodinger,
then also by Einstein, and will look on the arxiv for papers authored by Felix
Hummel. At the end, all these documents will be stored in the ``docs.yaml``.
After that we pick one document from them and store the information in
the file ``specially-picked-document.bib``, and we could go on and on.

If you want to follow-up on these documents and get them again to pick one,
you could use the ``yaml`` command to read in document information from a yaml
file, i.e., the previously created ``docs.yaml``

::

    papis explore \\
        yaml docs.yaml \\
        pick \\
        cmd 'papis scihub {doc[doi]}' \\
        cmd 'firefox {doc[url]}'

In this last example, we read the documents' information from ``docs.yaml`` and
pick a document, which then feed into the ``explore cmd`` command, that accepts
a papis formatting string to issue a general shell command.  In this case, the
picked document gets fed into the ``papis scihub`` command which tries to
download the document using ``scihub``, and also this very document is tried to
be opened by firefox (in case the document does have a ``url``).

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
import papis.cli
import click
import logging
import papis.commands.add
import papis.commands.export
import papis.api


logger = logging.getLogger('explore')


@click.group(invoke_without_command=False, chain=True)
@click.help_option('--help', '-h')
@click.pass_context
def cli(ctx):
    """
    Explore new documents using a variety of resources
    """
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
@click.option('--author', '-a', default=None)
@click.option('--title', '-t', default=None)
def isbnplus(ctx, query, author, title):
    """
    Look for documents on isbnplus.com

    Examples of its usage are

    papis explore isbnplus -q 'Albert einstein' pick cmd 'firefox {doc[url]}'

    """
    import papis.isbn
    logger = logging.getLogger('explore:isbnplus')
    logger.info('Looking up...')
    try:
        data = papis.isbn.get_data(
            query=query,
            author=author,
            title=title
        )
    except:
        data = []
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj['documents'] += docs
    logger.info('{} documents found'.format(len(docs)))


@cli.command('dissemin')
@click.pass_context
@click.help_option('--help', '-h')
@click.option('--query', '-q', default=None)
def dissemin(ctx, query):
    """
    Look for documents on dissem.in

    Examples of its usage are

    papis explore dissemin -q 'Albert einstein' pick cmd 'firefox {doc[url]}'

    """
    import papis.dissemin
    logger = logging.getLogger('explore:dissemin')
    logger.info('Looking up...')
    data = papis.dissemin.get_data(query=query)
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj['documents'] += docs
    logger.info('{} documents found'.format(len(docs)))


@cli.command('pick')
@click.pass_context
@click.help_option('--help', '-h')
def pick(ctx):
    """
    Pick a document from the retrieved documents

    Examples of its usage are

    papis explore bibtex lib.bib pick

    """
    docs = ctx.obj['documents']
    ctx.obj['documents'] = filter(
        lambda x: x is not None,
        [papis.api.pick_doc(docs)]
    )


@cli.command('bibtex')
@click.pass_context
@click.argument('bibfile', type=click.Path(exists=True))
@click.help_option('--help', '-h')
def bibtex(ctx, bibfile):
    """
    Import documents from a bibtex file

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


@cli.command('citations')
@click.pass_context
@papis.cli.query_option()
@click.help_option('--help', '-h')
@click.option(
    "--max-citations", "-m", default=-1,
    help='Number of citations to be retrieved'
)
def citations(ctx, query, max_citations):
    """
    Query the citations of a paper

    Example:

    Go through the citations of a paper and export it in a yaml file

        papis explore citations 'einstein' export --yaml einstein.yaml

    """
    from prompt_toolkit.shortcuts import ProgressBar
    import papis.crossref
    logger = logging.getLogger('explore:citations')

    documents = papis.api.get_documents_in_lib(
        papis.api.get_lib(),
        search=query
    )

    doc = papis.api.pick_doc(documents)
    db = papis.database.get()

    if not doc.has('citations') or doc['citations'] == []:
        logger.warning('No citations found')
        return

    dois = [d.get('doi') for d in doc['citations']]
    if max_citations < 0:
        max_citations = len(dois)
    dois = dois[0:min(max_citations, len(dois))]

    click.echo("%s citations found" % len(dois))
    click.echo("Fetching {} citations'".format(max_citations))
    dois_with_data = []

    with ProgressBar() as progress:
        for j, doi in progress(enumerate(dois), total=len(dois)):
            citation = db.query_dict(dict(doi=doi))

            if citation:
                dois_with_data.append(papis.api.pick_doc(citation))
            else:
                dois_with_data.append(
                    papis.crossref.doi_to_data(doi)
                )

    docs = [papis.document.Document(data=d) for d in dois_with_data]
    ctx.obj['documents'] += docs



@cli.command('yaml')
@click.pass_context
@click.argument('yamlfile', type=click.Path(exists=True))
@click.help_option('--help', '-h')
def yaml(ctx, yamlfile):
    """
    Import documents from a yaml file

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


@cli.command('json')
@click.pass_context
@click.argument('jsonfile', type=click.Path(exists=True))
@click.help_option('--help', '-h')
def json(ctx, jsonfile):
    """
    Import documents from a json file

    Examples of its usage are

    papis explore json lib.json pick

    """
    import json
    logger = logging.getLogger('explore:json')
    logger.info('Reading in json file {}'.format(jsonfile))
    docs = [
        papis.document.from_data(d) for d in json.load(open(jsonfile))
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
@click.option(
    "--json",
    help="Export list of documents retrieved to a json file",
    type=click.Path(),
    default=None
)
def export(ctx, bibtex, yaml, json):
    """
    Export retrieved documents into various formats for later use

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

    if json:
        with open(json, 'a+') as fd:
            logger.info(
                "Writing {} documents' json into {}".format(
                    len(docs),
                    json
                )
            )
            jsondata = papis.commands.export.run(docs, json=True)
            fd.write(jsondata)


@cli.command('cmd')
@click.pass_context
@click.help_option('--help', '-h')
@click.argument('command', type=str)
def cmd(ctx, command):
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
