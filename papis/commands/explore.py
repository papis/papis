"""
This command is mainly used to explore different databases and gather data
for a project before adding it to the Papis libraries.

Examples
^^^^^^^^

Imagine you want to search for some papers online but don't want to open the
browser to look for them. The ``explore`` command gives you a way to do this
using several online services. The command itself supports plugins, so see
``papis explore --help`` for a complete list of supported online services. A
summary can also be show with

.. code:: sh

    papis list --explorers

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
from papis.commands.export import available_formats
from papis.explorers import ExplorerLoaderGroup

logger = papis.logging.get_logger(__name__)


@click.group("explore",
             cls=ExplorerLoaderGroup,
             invoke_without_command=False, chain=True)
@click.help_option("--help", "-h")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    Explore new documents using a variety of resources.
    """
    ctx.obj = {"documents": []}


@cli.command("pick")
@click.pass_context
@click.help_option("-h", "--help")
@click.option(
    "-n",
    "--number",
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


@cli.command("add")
@click.pass_context
@click.help_option("-h", "--help")
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


@cli.command("cmd")
@click.pass_context
@click.help_option("-h", "--help")
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


@cli.command("export")
@click.pass_context
@click.help_option("--help", "-h")
@click.option(
    "-f", "--format", "fmt",
    help="Format for the document.",
    type=click.Choice(available_formats()),
    default="bibtex",)
@click.option(
    "-o",
    "--out",
    help="Outfile to write information to.",
    type=click.Path(),
    default=None,)
def explorer(ctx: click.Context, fmt: str, out: str) -> None:
    """
    Export retrieved documents into various formats.

    For example, to query Crossref and export all 200 documents to a YAML file,
    you can call:

    .. code:: sh

        papis explore \\
            crossref -m 200 -a 'Schrodinger' \\
            export --format yaml lib.yaml
    """
    docs = ctx.obj["documents"]

    from papis.commands.export import run

    outstring = run(docs, to_format=fmt)
    if out is not None:
        with open(out, "a+", encoding="utf-8") as fd:
            logger.info(
                "Writing %d documents in '%s' format to '%s'.", len(docs), fmt, out)
            fd.write(outstring)
    else:
        click.echo(outstring)
