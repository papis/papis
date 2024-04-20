"""
This command adds files to existing documents in a library.

Examples
^^^^^^^^

For instance imagine you have two PDF files, ``a.pdf`` and ``b.pdf``
that you want to add to a document that matches with the query string
"einstein photon definition". Then you would use

.. code:: sh

    papis addto 'einstein photon definition' -f a.pdf -f b.pdf

where the ``-f`` flag needs to be repeated for every file that is added. Remote
files can be similarly added using

.. code:: sh

    papis addto 'einstein photon definition' -u 'https://arxiv.org/pdf/2306.13122.pdf'

where the link needs to be to the actual remote PDF file.

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.addto:cli
    :prog: papis addto
"""

import os
from typing import List, Optional, Tuple

import click
import papis.api
import papis.cli
import papis.commands.add
import papis.config
import papis.document
import papis.git
import papis.logging
import papis.pick
import papis.strings
import papis.utils
from papis.exceptions import DocumentFolderNotFound

logger = papis.logging.get_logger(__name__)


def run(document: papis.document.Document,
        filepaths: List[str],
        link: bool = False,
        git: bool = False) -> None:
    doc_folder = document.get_main_folder()
    if not doc_folder or not os.path.exists(doc_folder):
        raise DocumentFolderNotFound(papis.document.describe(document))

    import shutil
    from papis.paths import symlink, rename_document_files

    new_file_list = rename_document_files(document, filepaths)

    for in_file_path, out_file_name in zip(filepaths, new_file_list):
        out_file_path = os.path.join(doc_folder, out_file_name)
        if os.path.exists(out_file_path):
            logger.warning("File '%s' already exists. Skipping...", out_file_path)
            continue

        if link:
            logger.info("[LN] '%s' to '%s'.", in_file_path, out_file_name)
            symlink(in_file_path, out_file_path)
        else:
            logger.info("[CP] '%s' to '%s'.", in_file_path, out_file_name)
            shutil.copy(in_file_path, out_file_path)

    if "files" not in document:
        document["files"] = []

    document["files"] += new_file_list
    papis.api.save_doc(document)

    if git:
        papis.git.add_and_commit_resources(
            doc_folder,
            new_file_list + [document.get_info_file()],
            "Add new files to '{}'".format(papis.document.describe(document)))


@click.command("addto")
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@papis.cli.git_option(help="Add and commit files")
@papis.cli.sort_option()
@click.option("-f",
              "--files",
              help="File fullpaths to documents",
              multiple=True,
              type=click.Path(exists=True))
@click.option("-u", "--urls", help="URLs to documents", multiple=True)
@click.option("--file-name",
              help="File name for the document (papis format)",
              default=None)
@click.option(
    "--link/--no-link",
    help="Instead of copying the file to the library, create a link to "
         "its original location",
    default=False)
@papis.cli.doc_folder_option()
def cli(query: str,
        git: bool,
        link: bool,
        files: List[str],
        urls: List[str],
        file_name: Optional[str],
        sort_field: Optional[str],
        doc_folder: Tuple[str, ...],
        sort_reverse: bool) -> None:
    """Add files to an existing document"""
    documents = papis.cli.handle_doc_folder_query_sort(
        query, doc_folder, sort_field, sort_reverse)

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    docs = papis.api.pick_doc(documents)

    if not docs:
        return

    document = docs[0]

    if file_name is not None:  # Use args if set
        papis.config.set("add-file-name", papis.config.escape_interp(file_name))

    try:
        run(document, files + urls, git=git, link=link)
    except Exception as exc:
        logger.error("Failed to add files.", exc_info=exc)
