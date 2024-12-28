"""
The ``open`` command is a very important command in the Papis workflow.
With it you can open documents, folders or marks.

Marks
^^^^^

One of special things about this command is the possibility of
creating marks for documents. As you would imagine, it is in general
difficult to create marks for any kind of data. For instance,
if our library consists of PDF files and EPUB files, we would like to define
bookmarks in order to go back to them at some later point.

How you define marks can be customized through the marks configuration
settings :ref:`here <marks-options>`. The default way of doing it is just by
defining a ``marks`` list in a document. Let us look at a concrete example:

.. code:: yaml

    author: Isaiah Shavitt, Rodney J. Bartlett
    edition: '1'
    files: [book.pdf]
    isbn: 052181832X,9780521818322

    marks:
    - {name: Intermediates definition, value: 344}
    - {name: EOM equations, value: 455}

    publisher: Cambridge University Press
    ref: book:293288
    series: Cambridge Molecular Science
    title: 'Many-Body Methods in Chemistry and Physics'
    type: book
    year: '2009'

This book has defined two marks. Each mark has a name and a value.
If you tell the ``open`` command to open marks, then it will look for
the marks and open the value (page number). This is the default behavior.
However, if you go to the :ref:`configuration <marks-options>`
you'll see that you can change the convention to what suits you.

Examples
^^^^^^^^

- Open a PDF file linked to a document matching the string ``bohm``

    .. code:: sh

        papis open bohm

- Open the folder where this last document is stored

    .. code:: sh

        papis open -d bohm

  The file browser used is given by the :confval:`file-browser` setting.

- Open a mark defined in the info file

    .. code:: sh

        papis open --mark bohm

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.open:cli
    :prog: papis open
"""

import os
from typing import Optional, Tuple

import click

import papis
import papis.api
import papis.pick
import papis.utils
import papis.config
import papis.cli
import papis.database
import papis.document
import papis.format
import papis.strings
import papis.logging
from papis.exceptions import DocumentFolderNotFound

logger = papis.logging.get_logger(__name__)


def run(document: papis.document.Document,
        opener: Optional[str] = None,
        folder: bool = False,
        mark: bool = False) -> None:
    if opener is not None:
        papis.config.set("opentool", papis.config.escape_interp(opener))

    doc_folder = document.get_main_folder()
    if doc_folder is None:
        raise DocumentFolderNotFound(papis.document.describe(document))

    if folder:
        # Open directory
        papis.api.open_dir(doc_folder)
    else:
        if mark:
            logger.debug("Getting document's marks.")
            marks = document[papis.config.getstring("mark-key-name")]
            if marks:
                mark_fmt = papis.config.getformattedstring("mark-header-format")
                mark_name = papis.config.getstring("mark-format-name")
                mark_opener = papis.config.getstring("mark-opener-format")
                if not mark_fmt:
                    raise ValueError(
                        "No mark header format given. Set 'mark-header-format' in "
                        "the configuration file")
                if not mark_name:
                    raise ValueError(
                        "No mark name format given. Set 'mark-format-name' "
                        "in the configuration file")
                mark_dict = papis.api.pick(
                    marks,
                    header_filter=lambda x: papis.format.format(
                        mark_fmt, x, doc_key=mark_name),
                    match_filter=lambda x: papis.format.format(
                        mark_fmt, x, doc_key=mark_name))
                if mark_dict:
                    if not mark_opener:
                        raise ValueError(
                            "No mark opener format given. Set 'mark-opener-format' "
                            "in the configuration file")
                    opener = papis.format.format(
                        mark_opener,
                        papis.document.from_data(mark_dict[0]),
                        doc_key=mark_name)
                    logger.info("Setting opener to '%s'.", opener)
                    papis.config.set("opentool", papis.config.escape_interp(opener))
        files = document.get_files()
        if not files:
            logger.error("The chosen document has no files attached: '%s'.",
                         papis.document.describe(document))
            return
        files_to_open = papis.api.pick(files, header_filter=os.path.basename)
        for file_to_open in files_to_open:
            papis.api.open_file(file_to_open, wait=False)


@click.command("open")
@click.help_option("-h", "--help")
@papis.cli.query_argument()
@papis.cli.sort_option()
@papis.cli.doc_folder_option()
@papis.cli.all_option()
@click.option(
    "--tool",
    help="Tool for opening the file (opentool)",
    default="")
@papis.cli.bool_flag(
    "-d", "--dir", "folder",
    help="Open directory")
@papis.cli.bool_flag(
    "-m", "--mark/--no-mark",
    help="Open mark",
    default=lambda: papis.config.getboolean("open-mark"))
def cli(query: str, doc_folder: Tuple[str, ...], tool: str, folder: bool,
        sort_field: Optional[str], sort_reverse: bool, _all: bool,
        mark: bool) -> None:
    """Open document from a given library"""
    if tool:
        papis.config.set("opentool", papis.config.escape_interp(tool))

    documents = papis.cli.handle_doc_folder_query_all_sort(query,
                                                           doc_folder,
                                                           sort_field,
                                                           sort_reverse,
                                                           _all)
    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    for document in documents:
        run(document, folder=folder, mark=mark)
