"""This command is to update the information of the documents.

Some examples of the usage are given below

Examples
^^^^^^^^

- Update a document automatically and interactively
  (searching by ``doi`` number in *crossref*, or in other sources...)

    .. code::

        papis update --auto -i "author : dyson"

- Update your library from a bib(la)tex file where many entries are listed.
  papis will try to look for documents in your library that match these
  entries and will ask you entry per entry to update it (of course this is
  done if you use the ``-i`` flag for interactively doing it). In the example
  ``libraryfile.bib`` is a file containing many entries.

    .. code::

        papis update --from bibtex libraryfile.bib -i

- Tag all einstein papers with the tag classics

    .. code::

        papis update --all --set tags classics einstein

and add the tag of ``physics`` to all papers tagged as ``classics``

    .. code::

        papis update --all --set tags '{doc[tags]} physics' einstein

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.update:cli
    :prog: papis update
"""

from typing import List, Dict, Tuple, Optional, Any

import click

import papis.utils
import papis.tui.utils
import papis.strings
import papis.downloaders
import papis.document
import papis.database
import papis.pick
import papis.format
import papis.cli
import papis.importer
import papis.git
import papis.logging
from papis.exceptions import DocumentFolderNotFound

logger = papis.logging.get_logger(__name__)


def _update_with_database(document: papis.document.Document) -> None:
    document.save()
    papis.database.get().update(document)


def run(document: papis.document.Document,
        data: Optional[Dict[str, Any]] = None,
        git: bool = False) -> None:
    if data is None:
        data = {}

    # Keep the ref the same, otherwise issues can be caused when
    # writing LaTeX documents and all the ref's change
    data["ref"] = document["ref"]
    document.update(data)
    _update_with_database(document)
    folder = document.get_main_folder()
    info = document.get_info_file()
    if not folder or not info:
        raise DocumentFolderNotFound(papis.document.describe(document))
    if git:
        papis.git.add_and_commit_resource(
            folder, info,
            "Update information for '{}'".format(
                papis.document.describe(document)))


@click.command("update")
@click.help_option("--help", "-h")
@papis.cli.git_option()
@papis.cli.query_argument()
@papis.cli.doc_folder_option()
@papis.cli.all_option()
@papis.cli.sort_option()
@click.option("--auto",
              help="Try to parse information from different sources",
              default=False,
              is_flag=True)
@click.option("--from", "from_importer",
              help="Add document from a specific importer ({0})".format(
                  ", ".join(papis.importer.available_importers())
              ),
              type=(click.Choice(papis.importer.available_importers()), str),
              nargs=2,
              multiple=True,
              default=(),)
@click.option("-s", "--set", "set_tuples",
              help="Update document's information with key value. "
                   "The value can be a papis format.",
              multiple=True,
              type=(str, str),)
def cli(query: str,
        git: bool,
        doc_folder: str,
        from_importer: List[Tuple[str, str]],
        auto: bool,
        _all: bool,
        sort_field: Optional[str],
        sort_reverse: bool,
        set_tuples: List[Tuple[str, str]],) -> None:
    """Update a document from a given library."""

    documents = papis.cli.handle_doc_folder_query_all_sort(query,
                                                           doc_folder,
                                                           sort_field,
                                                           sort_reverse,
                                                           _all)
    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    for document in documents:
        ctx = papis.importer.Context()

        logger.info("Updating {c.Back.WHITE}{c.Fore.BLACK}%s{c.Style.RESET_ALL}.",
                    papis.document.describe(document))

        ctx.data.update(document)
        if set_tuples:
            processed_tuples = {}
            for key, value in set_tuples:
                value = papis.format.format(value, document)
                if key == "notes":
                    value = papis.utils.clean_document_name(value)
                    processed_tuples[key] = value
                else:
                    processed_tuples[key] = value
            ctx.data.update(processed_tuples)

        # NOTE: use 'papis addto' to add files, so this only adds data
        # by setting 'only_data' to True always
        matching_importers = papis.utils.get_matching_importer_by_name(
            from_importer, only_data=True)

        if not from_importer and auto:
            for importer_cls in papis.importer.get_importers():
                try:
                    importer = importer_cls.match_data(document)
                    if importer:
                        try:
                            importer.fetch_data()
                        except NotImplementedError:
                            importer.fetch()
                except NotImplementedError:
                    continue
                except Exception as exc:
                    logger.exception("Failed to match document data.", exc_info=exc)
                else:
                    if importer and importer.ctx:
                        matching_importers.append(importer)

        imported = papis.utils.collect_importer_data(
            matching_importers, batch=False, only_data=True)
        ctx.data.update(imported.data)

        run(document, data=ctx.data, git=git)
