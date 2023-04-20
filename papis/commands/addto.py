"""
This command adds files to existing papis documents in some library.

For instance imagine you have two pdf files, ``a.pdf`` and ``b.pdf``
that you want to add to a document that matches with the query string
``einstein photon definition``, then you would use

::

    papis addto 'einstein photon definition' -f a.pdf -f b.pdf

notice that we repeat two times the flag ``-f``, this is important.

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.addto:cli
    :prog: papis addto
"""

import os
import tempfile
from typing import List, Optional

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
import requests
from papis.exceptions import DocumentFolderNotFound

logger = papis.logging.get_logger(__name__)


def run(document: papis.document.Document,
        filepaths: List[str],
        git: bool = False) -> None:
    doc_folder = document.get_main_folder()
    if not doc_folder or not os.path.exists(doc_folder):
        raise DocumentFolderNotFound(papis.document.describe(document))

    from papis.utils import create_identifier
    suffix = create_identifier(skip=len(document.get_files()))

    from papis.commands.add import get_file_name

    tmp_file = None
    new_file_list = []
    for in_file_path in filepaths:

        if in_file_path.startswith("http://") or in_file_path.startswith(
                "https://"):
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            try:
                resp = requests.get(in_file_path)
                if resp.status_code == 200:
                    tmp_file.write(resp.content)
                    tmp_file.close()
                    in_file_path = tmp_file.name
                else:
                    logger.warning("Failed to fetch '%s' (http error %d)",
                                   in_file_path, resp.status_code)
                    continue
            except requests.exceptions.RequestException as exc:
                logger.warning("Failed to fetch '%s'.",
                               in_file_path,
                               exc_info=exc)
                continue
            except Exception as e:
                logger.error("Failed to fetch '%s'.", in_file_path, exc_info=e)
                return

        if not os.path.exists(in_file_path):
            raise FileNotFoundError("File '{}' not found".format(in_file_path))

        # Rename the file in the staging area
        new_filename = get_file_name(
            papis.document.to_dict(document),
            in_file_path,
            suffix=next(suffix)
        )
        out_file_path = os.path.join(doc_folder, new_filename)
        new_file_list.append(new_filename)

        # Check if the absolute file path is > 255 characters
        if len(os.path.abspath(out_file_path)) >= 255:
            logger.warning(
                "Length of absolute path is > 255 characters. "
                "This may cause some issues with some PDF viewers.")

        if os.path.exists(out_file_path):
            logger.warning("File '%s' already exists. Skipping...", out_file_path)
            continue

        import shutil
        logger.info("[CP] '%s' to '%s'.", in_file_path, out_file_path)
        shutil.copy(in_file_path, out_file_path)

        if tmp_file:
            os.unlink(tmp_file.name)
            tmp_file = None

    if "files" not in document:
        document["files"] = []

    document["files"] += new_file_list
    papis.api.save_doc(document)

    if git:

        for r in new_file_list + [document.get_info_file()]:
            papis.git.add(doc_folder, r)
        papis.git.commit(
            doc_folder,
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
@papis.cli.doc_folder_option()
def cli(query: str,
        git: bool,
        files: List[str],
        urls: List[str],
        file_name: Optional[str],
        sort_field: Optional[str],
        doc_folder: str,
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
        papis.config.set("add-file-name", file_name)

    run(document, files + urls, git=git)
