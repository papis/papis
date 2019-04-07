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
import os
import papis.utils
import papis.commands
import papis.document
import papis.config
import papis.strings
import papis.cli
import click
import logging
import papis.commands.add
import papis.commands.export
import papis.api
import papis.pick
import papis.crossref
from stevedore import extension

logger = logging.getLogger('explore')
explorer_mgr = None


def stevedore_error_handler(manager, entrypoint, exception):
    logger = logging.getLogger('cmds:stevedore')
    logger.error("Error while loading entrypoint [%s]" % entrypoint)
    logger.error(exception)


def _create_explorer_mgr():
    global explorer_mgr

    if explorer_mgr is not None:
        return

    explorer_mgr = extension.ExtensionManager(
        namespace='papis.explorer',
        invoke_on_load=False,
        verify_requirements=True,
        propagate_map_exceptions=True,
        on_load_failure_callback=stevedore_error_handler
    )


def get_available_explorers():
    global explorer_mgr
    _create_explorer_mgr()
    return [e.plugin for e in explorer_mgr.extensions]


def get_explorer_mgr():
    global explorer_mgr
    _create_explorer_mgr()
    return explorer_mgr


@click.command('lib')
@click.pass_context
@click.help_option('--help', '-h')
@papis.cli.query_option()
@papis.cli.doc_folder_option()
@click.option('--library', '-l', default=None, help='Papis library to look')
def lib(ctx, query, doc_folder, library):
    """
    Query for documents in your library

    Examples of its usage are

        papis lib -l books einstein pick

    """
    logger = logging.getLogger('explore:lib')
    if doc_folder:
        ctx.obj['documents'] += [papis.document.from_folder(doc_folder)]
    db = papis.database.get(library=library)
    docs = db.query(query)
    logger.info('{} documents found'.format(len(docs)))
    ctx.obj['documents'] += docs
    assert(isinstance(ctx.obj['documents'], list))


@click.command('pick')
@click.pass_context
@click.help_option('--help', '-h')
@click.option(
    '--number', '-n',
    type=int,
    default=None,
    help='Pick automatically the n-th document'
)
def pick(ctx, number):
    """
    Pick a document from the retrieved documents

    Examples of its usage are

    papis explore bibtex lib.bib pick

    """
    docs = ctx.obj['documents']
    if number is not None:
        docs = [docs[number - 1]]
    doc = papis.pick.pick_doc(docs)
    if not doc:
        ctx.obj['documents'] = []
        return
    ctx.obj['documents'] = [doc]
    assert(isinstance(ctx.obj['documents'], list))


@click.command('citations')
@click.pass_context
@papis.cli.query_option()
@papis.cli.doc_folder_option()
@click.help_option('--help', '-h')
@click.option(
    "--save", "-s",
    is_flag=True,
    default=False,
    help="Store the citations in the document's folder for later use"
)
@click.option(
    "--rmfile",
    is_flag=True,
    default=False,
    help="Remove the stored citations file"
)
@click.option(
    "--max-citations", "-m", default=-1,
    help='Number of citations to be retrieved'
)
def citations(ctx, query, doc_folder, max_citations, save, rmfile):
    """
    Query the citations of a paper

    Example:

    Go through the citations of a paper and export it in a yaml file

        papis explore citations 'einstein' export --yaml einstein.yaml

    """
    import tqdm
    import colorama
    import papis.yaml
    logger = logging.getLogger('explore:citations')

    if doc_folder is not None:
        documents = [papis.document.from_folder(doc_folder)]
    else:
        documents = papis.api.get_documents_in_lib(
            papis.config.get_lib_name(),
            search=query
        )

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    doc = papis.pick.pick_doc(documents)
    if doc is None:
        return
    db = papis.database.get()
    citations_file = os.path.join(doc.get_main_folder(), 'citations.yaml')

    if os.path.exists(citations_file):
        if rmfile:
            logger.info('Removing {0}'.format(citations_file))
            os.remove(citations_file)
        else:
            logger.info(
                'A citations file exists in {0}'.format(citations_file)
            )
            if papis.utils.confirm('Do you want to use it?'):
                papis.yaml.explorer.callback(citations_file)
                return

    if not doc.has('citations') or doc['citations'] == []:
        logger.warning('No citations found')
        return

    dois = [d.get('doi') for d in doc['citations'] if d.get('doi')]
    if not dois:
        logger.error('No dois retrieved from the document\'s information')
        return

    if max_citations < 0:
        max_citations = len(dois)
    dois = dois[0:min(max_citations, len(dois))]

    logger.info("%s citations found" % len(dois))
    dois_with_data = []
    found_in_lib_dois = []

    logger.info("Checking which citations are already in the library")
    with tqdm.tqdm(iterable=dois) as progress:
        for doi in progress:
            citation = db.query_dict(dict(doi=doi))
            if citation:
                progress.set_description(
                    '{c.Fore.GREEN}{c.Back.BLACK}'
                    '{0: <22.22}'
                    '{c.Style.RESET_ALL}'
                    .format(doi, c=colorama)
                )
                dois_with_data.append(citation[0])
                found_in_lib_dois.append(doi)
            else:
                progress.set_description(
                    '{c.Fore.RED}{c.Back.BLACK}{0: <22.22}{c.Style.RESET_ALL}'
                    .format(doi, c=colorama)
                )

    for doi in found_in_lib_dois:
        dois.remove(doi)

    logger.info("Found {0} dois in library".format(len(found_in_lib_dois)))
    logger.info("Fetching {} citations from crossref".format(len(dois)))

    with tqdm.tqdm(iterable=dois) as progress:
        for doi in progress:
            data = papis.crossref.get_data(dois=[doi])
            progress.set_description(
                '{c.Fore.GREEN}{c.Back.BLACK}{0: <22.22}{c.Style.RESET_ALL}'
                .format(doi, c=colorama)
            )
            if data:
                assert(isinstance(data, list))
                dois_with_data.extend(data)

    docs = [papis.document.Document(data=d) for d in dois_with_data]
    if save:
        logger.info('Storing citations in "{0}"'.format(citations_file))
        with open(citations_file, 'a+') as fd:
            logger.info(
                "Writing {} documents' yaml into {}".format(
                    len(docs),
                    citations_file
                )
            )
            yamldata = papis.commands.export.run(docs, to_format='yaml')
            fd.write(yamldata)
    ctx.obj['documents'] += docs


@click.command('cmd')
@click.pass_context
@click.help_option('--help', '-h')
@click.argument('command', type=str)
def cmd(ctx, command):
    """
    Run a general command on the document list

    Examples of its usage are:

    Look for 200 Schroedinger papers, pick one, and add it via papis-scihub

    papis explore crossref -m 200 -a 'Schrodinger' \\
        pick cmd 'papis scihub {doc[doi]}'

    """
    from subprocess import call
    import shlex
    logger = logging.getLogger('explore:cmd')
    docs = ctx.obj['documents']
    for doc in docs:
        fcommand = papis.utils.format_doc(command, doc)
        splitted_command = shlex.split(fcommand)
        logger.info('Calling %s' % splitted_command)
        call(splitted_command)


@click.group("explore", invoke_without_command=False, chain=True)
@click.help_option('--help', '-h')
@click.pass_context
def cli(ctx):
    """
    Explore new documents using a variety of resources
    """
    ctx.obj = {'documents': []}


for _explorer in get_available_explorers():
    cli.add_command(_explorer)
