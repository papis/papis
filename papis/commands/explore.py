"""
This command is mainly used to explore different databases and gather data
for a project before adding it to the Papis libraries.

Examples
^^^^^^^^

Imagine you want to search for some papers online but don't want to open the
browser to look for them. The ``explore`` command gives you a way to do this
using several online services.

An excellent resource for this is `Crossref <https://www.crossref.org/>`__.
You can use it by using the ``crossref`` subcommand:

.. code:: sh

    papis explore crossref --author 'Freeman Dyson'

If you issue this command, you will see some text but basically nothing
will happen. This is because ``explore`` is conceived as a concatenating command.
Doing a simple:

.. code:: sh

    papis explore crossref -h

will tell you which commands are available. Let us suppose that you want to
look for some documents on Crossref, say some papers of Schrodinger's, and
you want to store them into a BibTeX file called ``lib.bib``. Then you could
concatenate the commands ``crossref`` and ``export --format bibtex``:

.. code:: sh

    papis explore crossref -a 'Schrodinger' export --format bibtex --out 'lib.bib'

This will store everything that you got from Crossref in the ``lib.bib`` file.
However, ``explore`` is much more flexible than that. You can also pick just
one document to store. For instance, let's assume that you don't want to store
all retrieved documents but only one that you pick. The ``pick`` command will
take care of it:

.. code:: sh

    papis explore crossref -a 'Schrodinger' pick export --format bibtex --out 'lib.bib'

Notice how the ``pick`` command is situated before the ``export``.
More generally you could write something like:

.. code:: sh

    papis explore \\
        crossref -a 'Schrodinger' \\
        crossref -a 'Einstein' \\
        arxiv -a 'Felix Hummel' \\
        export --format yaml --out 'docs.yaml' \\
        pick  \\
        export --format bibtex --out 'special-picked-documents.bib'

The upper command will look in Crossref for documents authored by Schrodinger,
then also by Einstein, and will look on the arXiv for papers authored by Felix
Hummel. At the end, all these documents will be stored in the ``docs.yaml`` file.
After that we pick one document from them and store the information in
the file ``special-picked-documents.bib``, and we could go on and on.

If you want to follow up on these documents and get them to pick one again,
you could use the ``yaml`` command to read in document information from a YAML
file, e.g. the previously created ``docs.yaml``:

.. code:: sh

    papis explore \\
        yaml 'docs.yaml' \\
        pick \\
        cmd 'papis scihub {doc[doi]}' \\
        cmd 'firefox {doc[url]}'

In this last example, we read the documents from ``docs.yaml`` and pick a
document, which we then feed into the ``explore cmd`` command.  This command
accepts a string to issue a general shell command and allows formatting with the
Papis format syntax.  In this case, the picked document gets fed into the
``papis scihub`` command which tries to download the document using ``scihub``.
Also this very document is opened by Firefox (in case the document does have a
``url``).

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.explore:cli
    :prog: papis explore
    :nested: full
"""

import shlex

import click

import papis.cli
import papis.logging
from papis.commands import AliasedGroup

logger = papis.logging.get_logger(__name__)

#: Name of the entrypoint group for explorer plugins.
EXPLORER_EXTENSION_NAME = "papis.explorer"


def get_available_explorers() -> list[click.Command]:
    """Gets all registered exporters."""
    from papis.plugin import get_plugins

    return list(get_plugins(EXPLORER_EXTENSION_NAME).values())


def get_explorer_by_name(name: str) -> click.Command:
    from papis.plugin import InvalidPluginTypeError, get_plugin_by_name

    cls = get_plugin_by_name(EXPLORER_EXTENSION_NAME, name)
    if not isinstance(cls, click.Command):
        raise InvalidPluginTypeError(EXPLORER_EXTENSION_NAME, name)

    return cls


@click.command("lib")
@click.pass_context
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@click.option("--library", "-l", default=None, help="Papis library to look in.")
def lib(ctx: click.Context,
        query: str,
        doc_folder: tuple[str, ...],
        library: str | None) -> None:
    """
    Query for documents in your library.

    For example, to query all the documents containing "einstein" in the "books"
    library, you can call:

    .. code:: sh

        papis explore lib -l books 'einstein' pick
    """

    from papis.document import from_folder

    if doc_folder:
        ctx.obj["documents"] += [from_folder(d) for d in doc_folder]

    from papis.database import get

    db = get(library_name=library)
    docs = db.query(query)
    logger.info("Found %d documents.", len(docs))

    ctx.obj["documents"] += docs
    assert isinstance(ctx.obj["documents"], list)


@click.command("pick")
@click.pass_context
@click.help_option("--help", "-h")
@click.option("--number", "-n",
              type=int,
              default=None,
              help="Automatically pick the n-th document.")
def pick(ctx: click.Context, number: int | None) -> None:
    """
    Pick a document from the retrieved documents.

    For example, to open a picker with the documents in a BibTeX file,
    you can call:

    .. code:: sh

        papis explore bibtex 'lib.bib' pick
    """
    from papis.api import pick_doc

    docs = ctx.obj["documents"]
    if number is not None:
        docs = [docs[number - 1]]

    picked_docs = pick_doc(docs)
    if not picked_docs:
        ctx.obj["documents"] = []
        return

    ctx.obj["documents"] = picked_docs


@click.command("citations")
@click.pass_context
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@click.help_option("--help", "-h")
@papis.cli.bool_flag("-b", "--cited-by",
                     help="Use the cited-by citations.")
@papis.cli.all_option()
def citations(ctx: click.Context,
              query: str,
              doc_folder: tuple[str, ...],
              cited_by: bool,
              _all: bool) -> None:
    """
    Query the citations for a paper.

    For example, to go through the citations of a paper and export it in a
    YAML file, you can call:

    .. code:: sh

        papis explore citations 'einstein' export --format yaml --out 'einstein.yaml'
    """

    from papis.api import get_documents_in_lib, pick_doc
    from papis.document import describe, from_folder

    if doc_folder is not None:
        documents = [from_folder(d) for d in doc_folder]
    else:
        from papis.config import get_lib_name

        documents = get_documents_in_lib(get_lib_name(), search=query)

    if not _all:
        documents = pick_doc(documents)  # type: ignore[assignment]

    if not documents:
        from papis.strings import no_documents_retrieved_message

        logger.warning(no_documents_retrieved_message)
        return

    from papis.citations import get_citations, get_cited_by

    for document in documents:
        logger.debug("Exploring document '%s'.", describe(document))

        citations = get_cited_by(document) if cited_by else get_citations(document)
        logger.debug("Found %d citations.", len(citations))

        ctx.obj["documents"].extend(citations)


@click.command("add")
@click.pass_context
def add(ctx: click.Context) -> None:
    """
    Add selected documents to the current library.

    For example, to add documents from a BibTeX file, you can call:

    .. code:: sh

        papis explore bibtex 'lib.bib' pick add
    """
    from papis.commands.add import run

    docs = ctx.obj["documents"]
    for d in docs:
        run([], d)


@click.command("cmd")
@click.pass_context
@click.help_option("--help", "-h")
@click.argument("command", type=papis.cli.FormatPatternParamType())
def cmd(ctx: click.Context, command: str) -> None:
    """
    Run a general command on the document list.

    For example, to look for 200 Schrodinger papers with
    `Crossref <https://www.crossref.org/>`__, pick one, and add it to the
    current library via ``papis-scihub``, you can call:

    .. code:: sh

        papis explore \\
            crossref -m 200 -a 'Schrodinger' \\
            pick \\
            cmd 'papis scihub {doc[doi]}'
    """
    from papis.format import format
    from papis.utils import run

    docs = ctx.obj["documents"]
    for doc in docs:
        fcommand = format(command, doc, default="")
        run(shlex.split(fcommand))


@click.group("explore",
             cls=AliasedGroup,
             invoke_without_command=False, chain=True)
@click.help_option("--help", "-h")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    Explore new documents using a variety of resources.
    """
    ctx.obj = {"documents": []}


for _explorer in get_available_explorers():
    cli.add_command(_explorer)
