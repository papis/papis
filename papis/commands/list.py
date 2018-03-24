"""
This command is to list contents of a library.

CLI Examples
^^^^^^^^^^^^

- List all document files associated will all entries:

    .. code:: bash

        papis list --file

    .. raw:: HTML

        <script type="text/javascript"
        src="https://asciinema.org/a/XwD0ZaUORoOonwDw4rXoQDkjZ.js"
        id="asciicast-XwD0ZaUORoOonwDw4rXoQDkjZ" async></script>

- List all document year and title with custom formatting:

    .. code:: bash

        papis list --format '{doc[year]} {doc[title]}'

    .. raw:: HTML

        <script type="text/javascript"
        src="https://asciinema.org/a/NZ8Ii1wWYPo477CIL4vZhUqOy.js"
        id="asciicast-NZ8Ii1wWYPo477CIL4vZhUqOy" async></script>

- List all documents according to the bibitem formatting (stored in a template
  file ``bibitem.template``):

    .. code:: bash

        papis list --template bibitem.template

    .. raw:: HTML

        <script type="text/javascript"
        src="https://asciinema.org/a/QZTBZ3tFfyk9WQuJ9WWB2UpSw.js"
        id="asciicast-QZTBZ3tFfyk9WQuJ9WWB2UpSw" async></script>

Python examples
^^^^^^^^^^^^^^^

.. code:: python

    # Import the run function from the list command

    from papis.commands.list import run as papis_list

    documents = papis_list(query='einstein', library='papis')

    for doc in documents:
        print(doc["url"])

    # etc...
    info_files = list(query='einstein', library='papis', info_files=True)

    # do something with the info file paths...

"""

import logging
import papis
from papis.api import status
import os
import papis.utils
import papis.config
import papis.database
import papis.downloaders.utils

logger = logging.getLogger('list')


def run(
        query="",
        library=papis.config.get_lib(),
        libraries=False,
        downloaders=False,
        pick=False,
        files=False,
        folders=False,
        info_files=False,
        fmt="",
        template=None
        ):
    """Main method to the list command

    :returns: List different objects
    :rtype:  list
    """
    config = papis.config.get_configuration()
    db = papis.database.get(library)
    if template is not None:
        if not os.path.exists(template):
            logger.error(
                "Template file %s not found" % template
            )
            return status.file_not_found
        fd = open(template)
        fmt = fd.read()
        fd.close()

    if downloaders:
        return papis.downloaders.utils.getAvailableDownloaders()

    if libraries:
        return [
            config[section]['dir']
            for section in config
            if 'dir' in config[section]
        ]

    documents = db.query(query)

    if pick:
        documents = [papis.api.pick_doc(documents)]

    if files:
        return [
            doc_file for files in [
                document.get_files() for document in documents
            ] for doc_file in files
        ]
    elif info_files:
        return [
            os.path.join(
                document.get_main_folder(),
                document.get_info_file()
            ) for document in documents
        ]
    elif fmt:
        return [
            papis.utils.format_doc(fmt, document)
            for document in documents
        ]
    elif folders:
        return [
            document.get_main_folder() for document in documents
        ]
    else:
        return documents


class Command(papis.commands.Command):
    def init(self):

        self.parser = self.get_subparsers().add_parser(
            "list",
            help="List documents from a given library"
        )

        self.add_search_argument()

        self.parser.add_argument(
            "-i",
            "--info",
            help="Show the info file name associated with the document",
            default=False,
            action="store_true"
        )

        self.parser.add_argument(
            "-f",
            "--file",
            help="Show the file name associated with the document",
            action="store_true"
        )

        self.parser.add_argument(
            "-d",
            "--dir",
            help="Show the folder name associated with the document",
            action="store_true"
        )

        self.parser.add_argument(
            "--format",
            help="List entries using a custom papis format, e.g."
            " '{doc[year] {doc[title]}",
            default=None,
            action="store"
        )

        self.parser.add_argument(
            "--template",
            help="Template file containing a papis format to list entries",
            default=None,
            action="store"
        )

        self.parser.add_argument(
            "-p",
            "--pick",
            help="Pick the document instead of listing everything",
            action="store_true"
        )

        self.parser.add_argument(
            "--downloaders",
            help="List available downloaders",
            action="store_true"
        )

        self.parser.add_argument(
            "--libraries",
            help="List defined libraries",
            action="store_true"
        )

    def main(self):

        if not self.args.libraries and \
            not self.args.downloaders and \
            not self.args.file and \
            not self.args.info and \
                not self.args.dir:
            self.args.dir = True

        objects = run(
            query=self.args.search,
            library=self.args.lib,
            libraries=self.args.libraries,
            downloaders=self.args.downloaders,
            pick=self.args.pick,
            files=self.args.file,
            folders=self.args.dir,
            info_files=self.args.info,
            fmt=self.args.format,
            template=self.args.template
        )
        for o in objects:
            print(o)
        return status.success
