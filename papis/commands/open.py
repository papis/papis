"""
The open command is a very important command in the papis workflow.
With it you can open documents, folders or marks.

Marks
^^^^^

One of special things about this command is the possibility of
creating marks for documents. As you would imagine, it is in general
difficult to create marks for any kind of data. For instance,
if our library consists of pdf files and epub files for instance,
we would like to define bookmarks in order to go back to them at
some later point.

How you define marks can be customized through the marks configuration
settings :ref:`here <marks-options>`.
The default way of doing it is just by defining a ``marks`` list in a document.
Let us look at a concrete example:

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
If you tell the open command to open marks, then it will look for
the marks and open the value (page number). This is the default behaviour,
however if you go to the :ref:`configuration <marks-options>`
you'll see that you can change the convention to what it suits you.


Examples
^^^^^^^^
- Open a pdf file linked to a document matching the string ``bohm``

    ::

        papis open bohm

- Open the folder where this last document is stored

    ::

        papis open -d bohm

  Please notice that the file browser used will be also related to
  the :ref:`file-browser setting <config-settings-file-browser>`.

- Open a mark defined in the info file

    ::

        papis open --mark bohm


Cli
^^^
.. click:: papis.commands.open:cli
    :prog: papis open
"""
import papis
import papis.api
import papis.utils
import papis.config
import papis.cli
import papis.database
import click
import logging


def run(document, opener=None, folder=False, mark=False):
    logger = logging.getLogger('open:run')
    if opener is not None:
        papis.config.set("opentool", opener)

    if folder:
        # Open directory
        papis.api.open_dir(document.get_main_folder())
    else:
        if mark:
            logger.debug("Getting document's marks")
            marks = document[papis.config.get("mark-key-name")]
            if marks:
                logger.debug("Picking marks")
                mark = papis.api.pick(
                    marks,
                    dict(
                        header_filter=lambda x: papis.utils.format_doc(
                            papis.config.get("mark-header-format"),
                            x, key=papis.config.get("mark-format-name")
                        ),
                        match_filter=lambda x: papis.utils.format_doc(
                            papis.config.get("mark-header-format"),
                            x, key=papis.config.get("mark-format-name")
                        )
                    )
                )
                if mark:
                    opener = papis.utils.format_doc(
                        papis.config.get("mark-opener-format"),
                        mark, key=papis.config.get("mark-format-name")
                    )
                    papis.config.set("opentool", opener)
        files = document.get_files()
        if len(files) == 0:
            logger.error("The document chosen has no files attached")
            return 1
        file_to_open = papis.api.pick(
            files,
            pick_config=dict(
                header_filter=lambda x: x.replace(
                    document.get_main_folder(), ""
                )
            )
        )
        papis.api.open_file(file_to_open, wait=False)


@click.command()
@click.help_option('-h', '--help')
@papis.cli.query_option()
@click.option(
    "--tool",
    help="Tool for opening the file (opentool)",
    default=""
)
@click.option(
    "-d",
    "--dir",
    help="Open directory",
    default=False,
    is_flag=True
)
@click.option(
    "--all",
    help="Open all matching documents",
    default=False,
    is_flag=True
)
@click.option(
    "-m",
    "--mark/--no-mark",
    help="Open mark",
    default=lambda: True if papis.config.get('open-mark') else False
)
def cli(query, tool, dir, all, mark):
    """Open document from a given library"""
    if tool:
        papis.config.set("opentool", tool)

    documents = papis.database.get().query(query)
    if not documents:
        click.echo("No documents found with that name.")
        return 1

    if not all:
        documents = [papis.api.pick_doc(documents)]
        documents = [d for d in documents if d]
        if not len(documents):
            return 0

    for document in documents:
        run(
            document,
            folder=dir,
            mark=mark
        )
