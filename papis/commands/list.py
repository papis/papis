"""
This command is to list contents of a library.

CLI Examples
^^^^^^^^^^^^

- List all document files associated will all entries:

    .. code:: bash

        papis list --all --file

    .. raw:: HTML

        <script type="text/javascript"
        src="https://asciinema.org/a/XwD0ZaUORoOonwDw4rXoQDkjZ.js"
        id="asciicast-XwD0ZaUORoOonwDw4rXoQDkjZ" async></script>

- List all document year and title with custom formatting:

    .. code:: bash

        papis list --all --format '{doc[year]} {doc[title]}'

    .. raw:: HTML

        <script type="text/javascript"
        src="https://asciinema.org/a/NZ8Ii1wWYPo477CIL4vZhUqOy.js"
        id="asciicast-NZ8Ii1wWYPo477CIL4vZhUqOy" async></script>

- List all documents according to the bibitem formatting (stored in a template
  file ``bibitem.template``):

    .. code:: bash

        papis list --all --template bibitem.template

    .. raw:: HTML

        <script type="text/javascript"
        src="https://asciinema.org/a/QZTBZ3tFfyk9WQuJ9WWB2UpSw.js"
        id="asciicast-QZTBZ3tFfyk9WQuJ9WWB2UpSw" async></script>

Cli
^^^
.. click:: papis.commands.list:cli
    :prog: papis list
"""

import logging
import papis
import os
import papis.utils
import papis.strings
import papis.config
import papis.database
import papis.document
import papis.downloaders
import papis.cli
import papis.pick
import papis.format
import click

from typing import List, Optional, Union, Sequence

logger = logging.getLogger('list')


def run(
        documents: List[papis.document.Document],
        libraries: bool = False,
        downloaders: bool = False,
        pick: bool = False,
        files: bool = False,
        folders: bool = False,
        info_files: bool = False,
        notes: bool = False,
        fmt: str = "",
        template: Optional[str] = None
        ) -> Sequence[Union[str, papis.document.Document]]:
    """Main method to the list command

    :returns: List different objects
    :rtype:  list
    """
    if downloaders:
        return [str(d) for d in papis.downloaders.get_available_downloaders()]

    if template is not None:
        if not os.path.exists(template):
            logger.error("Template file {} not found".format(template))
            return []
        with open(template) as fd:
            fmt = fd.read()

    if libraries:
        config = papis.config.get_configuration()
        return [
            section + ' ' + config[section]['dir']
            for section in config
            if 'dir' in config[section]]

    if files:
        return [
            doc_file for files in [
                document.get_files() for document in documents
            ] for doc_file in files
        ]
    elif notes:
        return [
            os.path.join(d.get_main_folder() or '', d["notes"])
            for d in documents
            if d.get_main_folder() is not None
            and d.has("notes") and isinstance(d["notes"], str)
            and os.path.exists(
                        os.path.join(d.get_main_folder() or '', d["notes"]))]
    elif info_files:
        return [d.get_info_file() for d in documents]
    elif fmt:
        return [
            papis.format.format(fmt, document)
            for document in documents
        ]
    elif folders:
        return [
            str(d.get_main_folder()) for d in documents
            if d.get_main_folder() is not None
        ]
    else:
        return documents


@click.command("list")
@click.help_option('--help', '-h')
@papis.cli.query_option()
@papis.cli.sort_option()
@click.option(
    "-i",
    "--info",
    help="Show the info file name associated with the document",
    default=False,
    is_flag=True)
@click.option(
    "-f", "--file", "_file",
    help="Show the file name associated with the document",
    default=False,
    is_flag=True)
@click.option(
    "-d", "--dir", "_dir",
    help="Show the folder name associated with the document",
    default=False,
    is_flag=True)
@click.option(
    "-n", "--notes",
    help="List notes files, if any",
    default=False,
    is_flag=True)
@click.option(
    "--format", "_format",
    help="List entries using a custom papis format, e.g."
    " '{doc[year] {doc[title]}",
    default='')
@click.option(
    "--template",
    help="Template file containing a papis format to list entries",
    default=None)
@click.option(
    "--downloaders",
    help="List available downloaders",
    default=False,
    is_flag=True)
@click.option(
    "--libraries",
    help="List defined libraries",
    default=False,
    is_flag=True)
@papis.cli.all_option()
def cli(
        query: str, info: bool, _file: bool, notes: bool, _dir: bool,
        _format: str,
        template: Optional[str], _all: bool, downloaders: bool,
        libraries: bool,
        sort_field: Optional[str], sort_reverse: bool) -> None:
    """List documents' properties"""

    logger = logging.getLogger('cli:list')
    documents = []  # type: List[papis.document.Document]

    if (not libraries and not downloaders and
            not _file and not info and not _dir):
        _dir = True

    if not libraries and not downloaders:
        db = papis.database.get()
        documents = db.query(query)
        if sort_field:
            documents = \
                papis.document.sort(documents, sort_field, sort_reverse)

        if not documents:
            logger.warning(papis.strings.no_documents_retrieved_message)
        if not _all:
            documents = list(papis.pick.pick_doc(documents))

    objects = run(
        documents,
        libraries=libraries,
        downloaders=downloaders,
        notes=notes,
        files=_file,
        folders=_dir,
        info_files=info,
        fmt=_format,
        template=template)

    for o in objects:
        click.echo(o)
