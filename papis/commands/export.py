"""
The ``export`` command is useful to work with other programs by exporting to
other formats (such as BibTeX).

Examples
^^^^^^^^

Some examples of its usage are:

- Export one of the documents matching the author with Einstein to BibTeX:

.. code:: sh

    papis export --format bibtex 'author : einstein'

- Note that BibTeX is the default format. The ``--format`` flag can be omitted:

.. code:: sh

    papis export 'author : einstein'

- Export all documents with author Einstein to BibTeX:

.. code:: sh

    papis export --all 'author : einstein'

- Export all documents in your default library to BibTeX and save them into a
  ``lib.bib`` file:

.. code:: sh

    papis export --all --out lib.bib

- Export a folder of one of the documents matching the word ``krebs``
  into a folder named ``interesting-document``:

.. code:: sh

    papis export --folder --out interesting-document krebs

This will create the folder ``interesting-document`` containing the
``info.yaml`` file and the linked documents.

.. note::

    Every document exported also comes with the key `_papis_local_folder`
    associated that points to the full local folder path where the document
    is stored in the file system. This is done for the convenience of third
    party apps.

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.export:cli
    :prog: papis export
"""

import os

import click

import papis
import papis.api
import papis.cli
import papis.database
import papis.document
import papis.logging
import papis.plugin
import papis.strings
import papis.tui.utils
import papis.utils
from papis.exceptions import DocumentFolderNotFound

logger = papis.logging.get_logger(__name__)

#: The entry point name for exporter plugins.
EXPORTER_EXTENSION_NAME = "papis.exporter"


def available_formats() -> list[str]:
    from papis.plugin import get_plugin_names

    return get_plugin_names(EXPORTER_EXTENSION_NAME)


def run(documents: list[papis.document.Document], to_format: str) -> str:
    """
    Exports several documents into something else.

    :param documents: A list of Papis documents
    :param to_format: what format to use
    """
    from papis.plugin import get_plugin_by_name

    exporter = get_plugin_by_name(EXPORTER_EXTENSION_NAME, to_format)
    if exporter is None:
        logger.error("Could not find exporter for format '%s'.", to_format)
        return ""

    try:
        result = exporter(documents)
    except KeyError as exc:
        logger.error("Failed to load '%s' exporter. Cannot export to this format.",
                     to_format, exc_info=exc)
        return ""

    if isinstance(result, str):
        return result
    else:
        logger.warning("Exporter for format '%s' did not return a string. This "
                       "is likely a bug!", to_format)
        return str(result)


@click.command("export")
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@papis.cli.sort_option()
@papis.cli.all_option()
@papis.cli.bool_flag(
    "--folder",
    help="Export document folder to share.")
@click.option(
    "-o",
    "--out",
    help="Outfile or outdir.",
    default=None)
@click.option(
    "-f",
    "--format", "fmt",
    help="Format for the document.",
    type=click.Choice(available_formats()),
    default="bibtex",)
@papis.cli.bool_flag(
    "-p",
    "--append",
    help="Append to outfile instead of overwriting.")
@papis.cli.bool_flag(
    "-b",
    "--batch",
    help="Do not prompt when overwriting a file.")
def cli(query: str,
        doc_folder: tuple[str, ...],
        sort_field: str | None,
        sort_reverse: bool,
        folder: str,
        out: str,
        fmt: str,
        append: bool,
        batch: bool,
        _all: bool) -> None:
    """Export a document from a given library."""

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

    if ret_string and not folder:
        if out is None:
            logger.info("Dumping to STDOUT.")
            click.echo(ret_string)
            return

        mode = "a" if append else "w"

        if os.path.exists(out):
            if append:
                msg = f"Appending to '{out}'."
            else:
                if not batch:
                    prompt = f"File '{out}' already exists. Overwrite?"
                    if not papis.tui.utils.confirm(prompt):
                        logger.info("Aborting.")
                        return
                msg = f"Overwriting '{out}'."
        else:
            msg = f"Writing to '{out}'."

        logger.info(msg)
        with open(out, mode, encoding="utf-8") as fd:
            fd.write(ret_string)

        return

    import shutil
    for document in documents:
        if folder:
            doc_main_folder = document.get_main_folder()
            if doc_main_folder is None:
                raise DocumentFolderNotFound(papis.document.describe(document))

            doc_main_folder_name = document.get_main_folder_name()
            if doc_main_folder_name is None:
                raise DocumentFolderNotFound(papis.document.describe(document))

            outdir = out or doc_main_folder_name
            if not len(documents) == 1:
                outdir = os.path.join(out, doc_main_folder_name)

            logger.info(
                "Exporting document '%s' to '%s'.",
                papis.document.describe(document), outdir)
            shutil.copytree(doc_main_folder, outdir)
