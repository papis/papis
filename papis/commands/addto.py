"""
This command adds files to existing documents in a library.

Examples
^^^^^^^^

For instance imagine you have two PDF files, ``a.pdf`` and ``b.pdf``
that you want to add to a document that matches with the query string
"einstein photon definition". Then you would use:

.. code:: sh

    papis addto 'einstein photon definition' -f a.pdf -f b.pdf

where the ``-f`` flag needs to be repeated for every file that is added. Remote
files can be similarly added using:

.. code:: sh

    papis addto 'einstein photon definition' -u 'https://arxiv.org/pdf/2306.13122.pdf'

where the link needs to be to the actual remote PDF file.

Command-line interface
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
        file_name: Optional[str] = None,
        link: bool = False,
        git: bool = False) -> None:
    doc_folder = document.get_main_folder()
    if not doc_folder or not os.path.exists(doc_folder):
        raise DocumentFolderNotFound(papis.document.describe(document))

    import shutil
    from papis.paths import (symlink, rename_document_files,
                             download_remote_files, is_remote_file)

    # ensure all remote files are downloaded, before we start renaming.
    local_files = download_remote_files(filepaths)

    # we only symlink a file it isn't a downloaded file that is stored in
    # a temporary directory. We keep track of a boolean per file that
    # tells us whether to link
    new_filepaths: List[Tuple[str, bool]] = []
    for orig_filepath, filepath in zip(filepaths, local_files):
        # skip remote files that haven't been properly downloaded
        if not filepath:
            continue

        if os.path.exists(filepath):
            new_filepaths.append((filepath,
                                  link if not is_remote_file(orig_filepath) else False))
        else:
            logger.warning("Skipping non-existent file: '%s'.", filepath)

    if not new_filepaths:
        logger.error("No valid files provided.")
        return

    # new_filenames is a list of renamed filenames. rename_document_files ensures
    # that here is no name collision even after renaming so we can be sure that
    # there is a unique filename for every file in the new_filepaths list.
    new_filenames = rename_document_files(
        document, [f[0] for f in new_filepaths],
        file_name_format=file_name, allow_remote=False,
    )
    assert len(new_filepaths) == len(new_filenames)

    for (in_file_path, link_file), out_file_name in zip(new_filepaths, new_filenames):

        out_file_path = os.path.join(doc_folder, out_file_name)
        if os.path.exists(out_file_path):
            logger.warning("File '%s' already exists. Skipping...", out_file_path)
            continue

        if link_file:
            logger.info("[LN] '%s' to '%s'.", in_file_path, out_file_name)
            symlink(in_file_path, out_file_path)
        else:
            logger.info("[CP] '%s' to '%s'.", in_file_path, out_file_name)
            shutil.copy(in_file_path, out_file_path)

    if "files" not in document:
        document["files"] = []

    document["files"] += new_filenames
    papis.api.save_doc(document)

    if git:
        papis.git.add_and_commit_resources(
            doc_folder,
            [*new_filenames, document.get_info_file()],
            f"Add new files to '{papis.document.describe(document)}'")


@click.command("addto")
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@papis.cli.git_option(help="Add and commit files.")
@papis.cli.sort_option()
@click.option("-f",
              "--files",
              help="File paths or URLs to documents.",
              multiple=True)
@click.option("-u", "--urls", help="(deprecated) use -f", multiple=True)
@click.option("--file-name",
              help="File name format for the document.",
              type=papis.cli.FormatPatternParamType(),
              default=None)
@click.option(
    "--link/--no-link",
    help="Instead of copying the file to the library, create a link to "
         "its original location.",
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
    """Add files to an existing document."""
    documents = papis.cli.handle_doc_folder_query_sort(
        query, doc_folder, sort_field, sort_reverse)

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    docs = papis.api.pick_doc(documents)

    if not docs:
        return

    document = docs[0]

    try:
        run(document, files + urls, file_name=file_name, git=git, link=link)
    except Exception as exc:
        logger.error("Failed to add files.", exc_info=exc)
