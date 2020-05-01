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

Cli
^^^
.. click:: papis.commands.update:cli
    :prog: papis update
"""

import click
import colorama
import logging

import papis.utils
import papis.tui.utils
import papis.strings
import papis.downloaders
import papis.document
import papis.database
import papis.pick
import papis.cli
import papis.importer
import papis.git

from typing import List, Dict, Tuple, Optional, Any


def _update_with_database(document: papis.document.Document) -> None:
    document.save()
    papis.database.get().update(document)


def run(document: papis.document.Document,
        data: Dict[str, Any] = dict(),
        git: bool = False) -> None:
    # Keep the ref the same, otherwise issues can be caused when
    # writing LaTeX documents and all the ref's change
    data['ref'] = document['ref']
    document.update(data)
    _update_with_database(document)
    folder = document.get_main_folder()
    info = document.get_info_file()
    if not folder or not info:
        raise Exception(papis.strings.no_folder_attached_to_document)
    if git:
        papis.git.add_and_commit_resource(
            folder, info,
            "Update information for '{0}'".format(
                papis.document.describe(document)))


@click.command("update")
@click.help_option('--help', '-h')
@papis.cli.git_option()
@papis.cli.query_option()
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
              help="Update document's information with key value."
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
    """Update a document from a given library"""

    logger = logging.getLogger('cli:update')

    if doc_folder:
        documents = [papis.document.from_folder(doc_folder)]
    else:
        documents = papis.database.get().query(query)

    if sort_field:
        documents = papis.document.sort(documents, sort_field, sort_reverse)

    if not _all:
        documents = list(papis.pick.pick_doc(documents))

    if not documents:
        logger.error(papis.strings.no_documents_retrieved_message)
        return

    for document in documents:
        ctx = papis.importer.Context()

        logger.info('Updating '
                    '{c.Back.WHITE}{c.Fore.BLACK}{0}{c.Style.RESET_ALL}'
                    .format(papis.document.describe(document), c=colorama))

        ctx.data.update(document)
        if set_tuples:
            ctx.data.update(
                {key: papis.document.format_doc(value, document)
                    for key, value in set_tuples})

        matching_importers = []
        if not from_importer and auto:
            for importer_cls in papis.importer.get_importers():
                try:
                    importer = importer_cls.match_data(document)
                    if importer:
                        importer.fetch()
                except NotImplementedError:
                    continue
                except Exception as e:
                    logger.exception(e)
                else:
                    if importer and importer.ctx:
                        matching_importers.append(importer)

        for _importer_name, _uri in from_importer:
            try:
                _uri = papis.document.format_doc(_uri, document)
                _iclass = papis.importer.get_importer_by_name(_importer_name)
                importer = _iclass(uri=_uri)
                importer.fetch()
                if importer.ctx:
                    matching_importers.append(importer)
            except Exception as e:
                logger.exception(e)

        if matching_importers:
            logger.info(
                'There are {0} possible matchings'
                .format(len(matching_importers)))

            for importer in matching_importers:
                if importer.ctx.data:
                    logger.info(
                        'Merging data from importer {0}'.format(importer.name))
                    papis.utils.update_doc_from_data_interactively(
                        ctx.data,
                        importer.ctx.data,
                        str(importer))
                if importer.ctx.files:
                    logger.info(
                        'Got files {0} from importer {1}'
                        .format(importer.ctx.files, importer.name))
                    for f in importer.ctx.files:
                        papis.utils.open_file(f)
                        if papis.tui.utils.confirm("Use this file?"):
                            ctx.files.append(f)

        run(document, data=ctx.data, git=git)
