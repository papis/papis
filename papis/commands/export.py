"""
The export command is useful to work with other programs such as bibtex.

Some examples of its usage are:

- Export one of the documents matching the author with einstein to bibtex:

.. code::

    papis export --bibtex 'author = einstein'

or export all of them

.. code::

    papis export --bibtex --all 'author = einstein'

- Export all documents to bibtex and save them into a ``lib.bib`` file

.. code::

    papis export --all --bibtex --out lib.bib

- Export a folder of one of the documents matching the word ``krebs``
  into a folder named, ``interesting-document``

.. code::

    papis export --folder --out interesting-document krebs

  this will create the folder ``interesting-document`` containing the
  ``info.yaml`` file, the linked documents and a ``bibtex`` file for
  sharing with other people.

  You can also just export its associated document:

.. code::

    papis export --file krebs


Cli
^^^
.. click:: papis.commands.export:cli
    :prog: papis export
"""
import papis
import os
import sys
import shutil
import papis.utils
import papis.document
import click
import papis.cli
import papis.api
import papis.database
import logging


def run(
    documents,
    yaml=False,
    bibtex=False,
    json=False,
    text=False
):
    """
    Exports several documents into something else.

    :param document: A ist of papis document
    :type  document: [papis.document.Document]
    :param yaml: Wether to return a yaml string
    :type  yaml: bool
    :param bibtex: Wether to return a bibtex string
    :type  bibtex: bool
    :param json: Wether to return a json string
    :type  json: bool
    :param text: Wether to return a text string representing the document
    :type  text: bool
    """
    if json:
        import json
        return json.dumps(
            [
                papis.document.to_dict(document) for document in documents
            ]
        )

    if yaml:
        import yaml
        return yaml.dump_all(
            [
                papis.document.to_dict(document) for document in documents
            ],
            allow_unicode=True
        )

    if bibtex:
        return '\n'.join([
            papis.document.to_bibtex(document) for document in documents
        ])

    if text:
        text_format = papis.config.get('export-text-format')
        return '\n'.join([
            papis.utils.format_doc(text_format, document)
            for document in documents
        ])

    return None


@click.command()
@click.help_option('--help', '-h')
@papis.cli.query_option()
@click.option(
    "--yaml",
    help="Export into yaml",
    default=False,
    is_flag=True
)
@click.option(
    "--bibtex",
    help="Export into bibtex",
    default=False,
    is_flag=True
)
@click.option(
    "--json",
    help="Export into json",
    default=False,
    is_flag=True
)
@click.option(
    "--folder",
    help="Export document folder to share",
    default=False,
    is_flag=True
)
@click.option(
    "--no-bibtex",
    help="When exporting to a folder, do not include the bibtex",
    default=False,
    is_flag=True
)
@click.option(
    "-o",
    "--out",
    help="Outfile or outdir",
    default=False,
    is_flag=True
)
@click.option(
    "-t",
    "--text",
    help="Text formated reference",
    default=False,
    is_flag=True
)
@click.option(
    "-a", "--all",
    help="Export all without picking",
    default=False,
    is_flag=True
)
@click.option(
    "--file",
    help="Export a copy of a file",
    default=False,
    is_flag=True
)
def cli(
        query,
        yaml,
        bibtex,
        json,
        folder,
        no_bibtex,
        out,
        text,
        all,
        file
        ):
    """Export a document from a given library"""

    logger = logging.getLogger('cli:export')
    documents = papis.database.get().query(query)

    if json and folder or yaml and folder:
        logger.warning("Only --folder flag will be considered")

    if not all:
        document = papis.api.pick_doc(documents)
        if not document:
            return 0
        documents = [document]

    if out and not folder and not file:
        logger.info("Dumping to {0}".format(out))
        out = open(out, 'a+')

    if not out and not folder and not file:
        logger.info("Dumping to stdout")
        out = sys.stdout

    ret_string = run(
        documents,
        yaml=yaml,
        bibtex=bibtex,
        json=json,
        text=text
    )

    if ret_string is not None:
        out.write(ret_string)
        return 0

    for document in documents:
        if folder:
            folder = document.get_main_folder()
            outdir = out or document.get_main_folder_name()
            if not len(documents) == 1:
                outdir = os.path.join(
                    outdir, document.get_main_folder_name()
                )
            shutil.copytree(folder, outdir)
            if not no_bibtex:
                open(
                    os.path.join(outdir, "info.bib"),
                    "a+"
                ).write(papis.document.to_bibtex(document))
        elif file:
            logger.info("Exporting file")
            files = document.get_files()
            files_to_open = [papis.api.pick(
                files,
                pick_config=dict(
                    header_filter=lambda x: x.replace(
                        document.get_main_folder(), ""
                    )
                )
            )]
            for file_to_open in filter(lambda x: x, files_to_open):
                logger.info("copy {0} to {1}".format(
                    file_to_open,
                    os.path.basename(file_to_open)
                ))
                shutil.copyfile(
                    file_to_open,
                    os.path.basename(file_to_open)
                )
