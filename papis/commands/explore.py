"""
This command can be used to explore documents from various sources to then act on them
in a number of ways.

The ``explore`` command should be thought of as a chain. The chain can contain various
subcommands that each act on what earlier subcommands have done. Subcommands come in
three varieties. First are *producers*: they add to the list of documents on which the
chain operates. These include subcommands that search online databases (``arxiv``,
``crossref``, ``dblp``, ``isbn``), parsers for various file formats (``bibtex``,
``yaml``, ``json``), and ``lib``, which searches local libraries. Second are
*transformers*: they read the list of documents produced earlier in the chain and
transform it into another list. These include ``citations``, which retrieves documents'
citations, and ``pick``, which allows selecting documents from among the results. Third
are *actions*: they act on the list of documents in various ways. These include ``add``,
``cmd``, and ``export``.

The ``explore`` command supports plugins, so see ``papis explore --help`` for a complete
list of supported sources.

Examples
^^^^^^^^

Imagine you want to search for papers online but don't want to open the browser to look
for them. The ``explore`` command gives you a way to do this using several online
services. An excellent resource for this is `Crossref <https://www.crossref.org/>`__.
You can use it with the ``crossref`` subcommand:

.. code:: sh

    papis explore crossref --query Schrodinger

If you issue this command, you will see some text but not much more. This is because
we've not chained another command to act on the results of our search. Let us suppose
that you want to select some of the results and add them to your library. You can
achieve this by adding the ``pick`` and ``add`` subcommands:

.. code:: sh

    papis explore crossref --query Schrodinger pick add

When you do this, your picker will open with the results of your search, and after
selecting documents, these will be added to your library. Notice how the ``pick``
subcommand is situated before the ``add``: it keeps only the picked documents, so
everything chained after it acts on that selection.

Similarly, if you instead wanted to export all of the search results to a BibTeX file,
you could use the ``export`` subcommand:

.. code:: sh

    papis explore crossref --query Schrodinger export --format bibtex --out 'lib.bib'

This will store everything that you got from Crossref in the ``lib.bib`` file.

Some sources also support the use of filters for structured searches. For instance,
rather than just a simple full-text search for 'Schrodinger', we can also search for
documents that have 'Schrodinger' as an author:

.. code:: sh

    papis explore crossref --filter author:Schrodinger \\
        export --format bibtex --out 'lib.bib'

Check the subcommand help texts (e.g., ``papis explore crossref --help``) to see what
filters a given source supports. A single search can have multiple filters. Filters
with different keys are combined with AND and multiple values of the same key with OR.

The ``explore`` command is very flexible, and you can chain together many subcommands
to achieve your goal. For instance, you could do:

.. code:: sh

    papis explore \\
        crossref --filter author:Schrodinger \\
        crossref --filter author:Einstein \\
        arxiv --filter author:'Felix Hummel' \\
        export --format yaml --out 'docs.yaml' \\
        pick  \\
        export --format bibtex --out 'special-picked-documents.bib'

The above command will search Crossref for documents authored by Schrodinger and
Einstein and arXiv for papers authored by Felix Hummel. It will store all these
documents in a ``docs.yaml`` file. Then, it will open the picker with these documents
so you can select some, which will be stored in ``special-picked-documents.bib``.

If you want to follow up on these documents, you can use the ``yaml`` subcommand to
read in document information from the YAML file:

.. code:: sh

    papis explore \\
        yaml 'docs.yaml' \\
        pick \\
        cmd 'firefox {doc[url]}'

Here, we read the documents from ``docs.yaml`` and pick a document, which we then feed
into the ``cmd`` subcommand. This command accepts a string to issue a shell command and
allows formatting with the Papis formatting patterns. In this case, the picked document
is opened with Firefox (if it has a ``url``).

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.explore:cli
    :prog: papis explore
    :nested: full
"""
from __future__ import annotations

import shlex
import subprocess
from typing import TYPE_CHECKING

import click

import papis.cli
import papis.logging
from papis.sources.client import log_source_result
from papis.sources.search import DEFAULT_MAX_RESULTS

if TYPE_CHECKING:
    from papis.document import Document
    from papis.sources.handler import SourceHandler

logger = papis.logging.get_logger(__name__)


def _make_search_command(handler: type[SourceHandler]) -> click.Command:
    """Build the search subcommand for *handler*."""
    filter_help = (
        f"Constrain the search. Supported fields: {', '.join(handler.search_fields)}."
        if handler.search_fields
        else "Constrain the search. This source does not support filters."
    )

    @click.command(handler.name, help=handler.__doc__)
    @click.option(
        "-q", "--query", default="",
        help="Query to search for. Optional if filters are given.")
    @click.option(
        "-f", "--filter", "filters", metavar="KEY:VALUE",
        help=filter_help,
        multiple=True)
    @click.option(
        "-m", "--max", "max_results",
        help="Maximum number of results.",
        default=DEFAULT_MAX_RESULTS,
        type=click.IntRange(1),
        show_default=True)
    @click.pass_context
    def command(ctx: click.Context,
                query: str,
                filters: tuple[str, ...],
                max_results: int) -> None:
        from papis.document import Document, from_data
        from papis.sources.client import search_item
        from papis.sources.handler import SearchInput

        filters_dict: dict[str, list[str]] = {}
        for item in filters:
            key, sep, value = item.partition(":")
            key = key.strip()
            value = value.strip()
            if not (sep and key and value):
                logger.error("Malformed filter '%s': expected 'KEY:VALUE'.", item)
                ctx.exit(1)

            filters_dict.setdefault(key, []).append(value)

        logger.info("Searching '%s' for documents.", handler.name)

        try:
            results = search_item(
                SearchInput(input=query.strip(), filters=filters_dict),
                (handler.name,),
                max_results=max_results,
            )
        except ValueError as exc:
            logger.error("%s", exc)
            ctx.exit(1)

        for result in results:
            if result.status != "ok":
                log_source_result(logger, result, sources={handler.name})
                continue

            docs = [d.copy() if isinstance(d, Document) else from_data(d)
                    for d in result.documents]

            ctx.obj["documents"].extend(docs)
            logger.info("Found %d documents from source '%s'.", len(docs),
                        result.source)
            if result.message:
                logger.warning("Source '%s': %s", result.source, result.message)

    return command


def _make_parse_command(handler: type[SourceHandler]) -> click.Command:
    """Build the content-format subcommand for *handler*."""
    @click.command(handler.name, help=handler.__doc__)
    @click.argument("file", type=click.Path(exists=True, dir_okay=False))
    @click.pass_context
    def command(ctx: click.Context, file: str) -> None:
        from papis.document import from_data
        from papis.gather import read_content
        from papis.sources.handler import ParseInput
        from papis.sources.parse import parse

        logger.info("Parsing documents from '%s'.", file)

        content = read_content(file)
        if content is None:
            logger.warning("Could not parse '%s': not readable as text.", file)
            return

        if not content:
            logger.warning("No documents found in '%s'.", file)
            return

        for result in parse(ParseInput(content=content), sources=(handler.name,)):
            if result.status != "ok":
                log_source_result(logger, result, sources={handler.name})
                if result.status in {"no_match", "no_result"}:
                    logger.warning("No documents found in '%s'.", file)
                return

            docs = [from_data(d) for d in result.documents]

            ctx.obj["documents"].extend(docs)
            logger.info("Found %d documents from source '%s'.", len(docs), handler.name)
            if result.message:
                logger.warning("Source '%s': %s", result.source, result.message)

    return command


def _get_source_handlers() -> dict[str, type[SourceHandler]]:
    """Map subcommand names to their source handlers."""
    from papis.sources.client import get_known_sources

    return {
        handler.name: handler
        for handler in get_known_sources()
        if {"search", "parse"} & handler.capabilities
    }


class ExploreGroup(click.Group):
    """A click chain group including subcommands for parse/search source handlers."""

    def list_commands(self, ctx: click.Context) -> list[str]:
        return sorted(set(super().list_commands(ctx)) | set(_get_source_handlers()))

    def get_command(self, ctx: click.Context,
                    cmd_name: str) -> click.Command | None:
        command = super().get_command(ctx, cmd_name)
        if command is not None:
            return command

        handler = _get_source_handlers().get(cmd_name)
        if handler is None:
            return None

        if "search" in handler.capabilities:
            return _make_search_command(handler)

        return _make_parse_command(handler)


@click.group(
    "explore",
    invoke_without_command=False, chain=True,
    cls=ExploreGroup)
@click.help_option("--help", "-h")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    Explore new documents from a variety of sources.
    """
    ctx.obj = {"documents": []}


@cli.command("citations")
@papis.cli.bool_flag(
    "-b",
    "--cited-by",
    help="Explore the cited-by citations.")
@click.pass_context
def citations(ctx: click.Context, cited_by: bool) -> None:
    """Get the citations of the current documents."""
    from papis.citations import get_citations, get_cited_by
    from papis.document import describe, from_data
    from papis.utils import locate_document

    documents = ctx.obj["documents"]
    if not documents:
        logger.warning("No documents selected with which to explore citations.")
        return

    found_citations: list[Document] = []
    for document in documents:
        logger.debug("Exploring document '%s'.", describe(document))

        found = get_cited_by(document) if cited_by else get_citations(document)
        logger.debug("Found %d citations.", len(found))

        for data in found:
            citation = from_data(data)
            if locate_document(citation, found_citations) is not None:
                logger.debug("Skipping duplicate citation for '%s'.",
                             describe(citation))
                continue

            found_citations.append(citation)

    if not found_citations:
        from papis.strings import no_documents_retrieved_message

        logger.warning(no_documents_retrieved_message)

    ctx.obj["documents"] = found_citations


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
    """Select documents from the retrieved documents."""
    from papis.api import pick_doc

    docs = ctx.obj["documents"]
    if number is not None:
        docs = [docs[number - 1]]

    ctx.obj["documents"] = pick_doc(docs)


@cli.command("add")
@click.pass_context
@click.help_option("-h", "--help")
def add(ctx: click.Context) -> None:
    """ Add selected documents to the current library."""
    from papis.commands.add import run

    docs = ctx.obj["documents"]
    for d in docs:
        run(d.get_files(), d)


@cli.command("cmd")
@papis.cli.bool_flag(
    "--batch",
    help="Skip documents whose command fails rather than aborting.")
@click.pass_context
@click.help_option("-h", "--help")
@click.argument("command", type=papis.cli.FormatPatternParamType())
def cmd(ctx: click.Context, command: str, batch: bool) -> None:
    """
    Run a shell command on the document list.

    The command may use each document's metadata through Papis formatting patterns.
    """
    from papis.format import format
    from papis.utils import run

    docs = ctx.obj["documents"]
    for doc in docs:
        fcommand = format(command, doc, default="")
        try:
            run(shlex.split(fcommand))
        except subprocess.CalledProcessError as exc:
            msg = "Command '%s' exited with code %d."
            if batch:
                logger.warning(msg, fcommand, exc.returncode)
                continue

            logger.error(msg, fcommand, exc.returncode)
            raise


@cli.command("export")
@click.pass_context
@click.help_option("--help", "-h")
@click.option(
    "-f", "--format", "fmt",
    help="Export format for document metadata.",
    type=str,
    default="bibtex",
)
@papis.cli.bool_flag("--list-exporters", help="List all supported exporters.")
@click.option(
    "-o",
    "--out",
    help="Output file for document metadata.",
    type=click.Path(),
    default=None,
)
def export(ctx: click.Context,
           fmt: str,
           list_exporters: bool,
           out: str) -> None:
    """Export retrieved documents into various formats."""
    if list_exporters:
        from papis.commands.list import list_plugins
        for o in list_plugins(show_exporters=True, verbose=True):
            click.echo(o)
        return

    from papis.exporters import get_available_exporters
    known_exporters = get_available_exporters()

    if fmt not in known_exporters:
        logger.error("Unknown export format: '%s'.", fmt)
        logger.error("Supported formats are: ['%s'].", "', '".join(known_exporters))
        ctx.exit(1)

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
