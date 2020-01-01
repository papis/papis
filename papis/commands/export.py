"""
The export command is useful to work with other programs such as bibtex.

Some examples of its usage are:

- Export one of the documents matching the author with einstein to bibtex:

.. code::

    papis export --format bibtex 'author : einstein'

or export all of them

.. code::

    papis export --format bibtex --all 'author : einstein'

- Export all documents to bibtex and save them into a ``lib.bib`` file

.. code::

    papis export --all --format bibtex --out lib.bib

- Export a folder of one of the documents matching the word ``krebs``
  into a folder named, ``interesting-document``

.. code::

    papis export --folder --out interesting-document krebs

  this will create the folder ``interesting-document`` containing the
  ``info.yaml`` file, the linked documents and a ``bibtex`` file for
  sharing with other people.


Cli
^^^
.. click:: papis.commands.export:cli
    :prog: papis export
"""
import papis
import os
import shutil
import papis.utils
import papis.document
import click
import papis.cli
import papis.api
import papis.database
import papis.strings
import logging
from stevedore import extension
import papis.plugin

logger = logging.getLogger('cli:export')
exporters_mgr = None


def export_to_yaml(documents):
    import yaml
    return yaml.dump_all(
        [
            papis.document.to_dict(document) for document in documents
        ],
        allow_unicode=True
    )


def export_to_json(documents):
    import json
    return json.dumps(
        [
            papis.document.to_dict(document) for document in documents
        ]
    )


def export_to_bibtex(documents):
    return '\n'.join([
        papis.document.to_bibtex(document) for document in documents
    ])


def available_formats():
    global exporters_mgr
    _create_mgr()
    return exporters_mgr.entry_points_names()



def _create_mgr():
    global exporters_mgr
    if exporters_mgr:
        return
    exporters_mgr = extension.ExtensionManager(
        namespace='papis.exporter',
        invoke_on_load=False,
        verify_requirements=True,
        propagate_map_exceptions=True,
        on_load_failure_callback=papis.plugin.stevedore_error_handler
    )


def run(
    documents,
    to_format,
):
    """
    Exports several documents into something else.

    :param document: A ist of papis document
    :type  document: [papis.document.Document]
    :param to_format: what format to use
    :type  to_format: str
    """
    global exporters_mgr
    _create_mgr()
    try:
        ret_string = exporters_mgr[to_format].plugin(
            document for document in documents
        )
        return ret_string
    except KeyError as e:
        logger.error("Format %s not supported." % to_format)

    return None


@click.command("export")
@click.help_option('--help', '-h')
@papis.cli.query_option()
@papis.cli.sort_option()
@papis.cli.all_option()
@click.option(
    "--folder",
    help="Export document folder to share",
    default=False,
    is_flag=True)
@click.option(
    "-o",
    "--out",
    help="Outfile or outdir",
    default=None)
@click.option(
    "-f",
    "--format",
    help="Format for the document",
    type=click.Choice(available_formats()),
    default="bibtex",)
def cli(
        query,
        folder,
        out,
        format,
        _all,
        sort_field,
        sort_reverse,
        **kwargs
        ):
    """Export a document from a given library"""

    documents = papis.database.get().query(query)

    if format and folder:
        logger.warning("Only --folder flag will be considered")

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    if not _all:
        document = papis.pick.pick_doc(documents)
        if not document:
            return 0
        documents = [document]

    if sort_field:
        documents = papis.document.sort(documents, sort_field, sort_reverse)

    ret_string = run(documents, to_format=format)

    if ret_string is not None and not folder:
        if out is not None:
            logger.info("Dumping to {0}".format(out))
            with open(out, 'a+') as fd:
                fd.write(ret_string)
        else:
            logger.info("Dumping to stdout")
            print(ret_string)
        return 0

    for document in documents:
        if folder:
            folder = document.get_main_folder()
            outdir = out or document.get_main_folder_name()
            if not len(documents) == 1:
                outdir = os.path.join(
                    (out or ''), document.get_main_folder_name()
                )
            logger.info("Exporting doc {0} to {1}".format(
                papis.document.describe(document), outdir
            ))
            shutil.copytree(folder, outdir)


@click.command('export')
@click.pass_context
@click.help_option('--help', '-h')
@click.option(
    "-f",
    "--format",
    help="Format for the document",
    type=click.Choice(available_formats()),
    default="bibtex",
)
@click.option(
    "-o",
    "--out",
    help="Outfile to write information to",
    type=click.Path(),
    default=None,
)
def explorer(ctx, format, out):
    """
    Export retrieved documents into various formats for later use

    Examples of its usage are

    papis explore crossref -m 200 -a 'Schrodinger' export --yaml lib.yaml

    """
    logger = logging.getLogger('explore:yaml')
    docs = ctx.obj['documents']

    outstring = run(docs, to_format=format)
    if out is not None:
        with open(out, 'a+') as fd:
            logger.info(
                "Writing {} documents' in {} into {}".format(
                    len(docs),
                    format,
                    out
                )
            )
            fd.write(outstring)
    else:
        print(outstring)
