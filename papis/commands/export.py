"""
The export command is useful to work with other programs such as bibtex.

Some examples of its usage are:

- Export one of the documents matching the author with einstein to bibtex:

.. code::

    papis export --format bibtex 'author : einstein'

or export all of them

.. code::

    papis export --format bibtex --all 'author : einstein'

- Export all documents to bibtex and save them into a ``lib.bib`` file

.. code::

    papis export --all --format bibtex --out lib.bib

- Export a folder of one of the documents matching the word ``krebs``
  into a folder named, ``interesting-document``

.. code::

    papis export --folder --out interesting-document krebs

  this will create the folder ``interesting-document`` containing the
  ``info.yaml`` file, the linked documents and a ``bibtex`` file for
  sharing with other people.

.. note::

    Every document exported also comes with the key `_papis_local_folder`
    associated that points to the full local folder path where the document
    is stored in the file system. This is done for the convenience of third
    party apps.


Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.export:cli
    :prog: papis export
"""

import os
from typing import List, Optional

import click

import papis
import papis.utils
import papis.document
import papis.cli
import papis.api
import papis.database
import papis.strings
import papis.plugin
import papis.logging
from papis.exceptions import DocumentFolderNotFound

logger = papis.logging.get_logger(__name__)


def available_formats() -> List[str]:
    return papis.plugin.get_available_entrypoints(_extension_name())


def _extension_name() -> str:
    return "papis.exporter"


def run(documents: List[papis.document.Document], to_format: str) -> str:
    """
    Exports several documents into something else.

    :param documents: A list of papis documents
    :param to_format: what format to use
    """
    ret_string = (
        papis.plugin.get_extension_manager(_extension_name())[to_format]
        .plugin(document for document in documents))
    return str(ret_string)


@click.command("export")
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@papis.cli.sort_option()
@papis.cli.all_option()
@click.option(
    "--folder",
    help="Export document folder to share",
    default=False,
    is_flag=True)
@click.option(
    "-o",
    "--out",
    help="Outfile or outdir",
    default=None)
@click.option(
    "-f",
    "--format", "fmt",
    help="Format for the document",
    type=click.Choice(available_formats()),
    default="bibtex",)
def cli(query: str,
        doc_folder: str,
        sort_field: Optional[str],
        sort_reverse: bool,
        folder: str,
        out: str,
        fmt: str,
        _all: bool) -> None:
    """Export a document from a given library"""

    documents = papis.cli.handle_doc_folder_query_all_sort(query,
                                                           doc_folder,
                                                           sort_field,
                                                           sort_reverse,
                                                           _all)
    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    if fmt and folder:
        logger.warning("Only --folder flag will be considered (--fmt ignored).")

    # Get the local folder of the document so that third-party apps
    # can actually go to the folder without checking with papis
    for d in documents:
        d["_papis_local_folder"] = d.get_main_folder()

    ret_string = run(documents, to_format=fmt)

    if ret_string is not None and not folder:
        if out is not None:
            logger.info("Dumping to '%s'.", out)
            with open(out, "a+") as fd:
                fd.write(ret_string)
        else:
            logger.info("Dumping to STDOUT.")
            click.echo(ret_string)
        return

    import shutil
    for document in documents:
        if folder:
            _doc_folder = document.get_main_folder()
            _doc_folder_name = document.get_main_folder_name()
            outdir = out or _doc_folder_name
            if not _doc_folder or not _doc_folder_name or not outdir:
                raise DocumentFolderNotFound(papis.document.describe(document))
            if not len(documents) == 1:
                outdir = os.path.join(out, _doc_folder_name)
            logger.info(
                "Exporting document '%s' to '%s'.",
                papis.document.describe(document), outdir)
            shutil.copytree(_doc_folder, outdir)


@click.command("export")
@click.pass_context
@click.help_option("--help", "-h")
@click.option(
    "-f", "--format", "fmt",
    help="Format for the document",
    type=click.Choice(available_formats()),
    default="bibtex",)
@click.option(
    "-o",
    "--out",
    help="Outfile to write information to",
    type=click.Path(),
    default=None,)
def explorer(ctx: click.Context, fmt: str, out: str) -> None:
    """
    Export retrieved documents into various formats for later use

    Examples of its usage are

    papis explore crossref -m 200 -a 'Schrodinger' export --yaml lib.yaml

    """
    docs = ctx.obj["documents"]

    outstring = run(docs, to_format=fmt)
    if out is not None:
        with open(out, "a+") as fd:
            logger.info(
                "Writing %d documents in '%s' format to '%s'.", len(docs), fmt, out)
            fd.write(outstring)
    else:
        click.echo(outstring)
