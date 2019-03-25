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

logger = logging.getLogger('cli:export')

def stevedore_error_handler(manager, entrypoint, exception):
    logger.error("Error while loading entrypoint [%s]" % entrypoint)
    logger.error(exception)


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
    return exporters_mgr.entry_points_names()

exporters_mgr = extension.ExtensionManager(
    namespace='papis.exporter',
    invoke_on_load=False,
    verify_requirements=True,
    propagate_map_exceptions=True,
    on_load_failure_callback=stevedore_error_handler
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
    try:
        ret_string = exporters_mgr[to_format].plugin(document for document in documents)
        return ret_string
    except KeyError as e:
        logger.error("Format %s not supported." % to_format)

    return None


@click.command("export")
@click.help_option('--help', '-h')
@papis.cli.query_option()
@click.option(
    "--folder",
    help="Export document folder to share",
    default=False,
    is_flag=True
)
@click.option(
    "-o",
    "--out",
    help="Outfile or outdir",
    default=None
)
@click.option(
    "--format",
    "-f",
    help="Text formated reference",
    type=click.Choice(available_formats()),
    default="bibtex",
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
        folder,
        out,
        format,
        all,
        file,
        **kwargs
        ):
    """Export a document from a given library"""

    documents = papis.database.get().query(query)

    if format == "json" and folder or format == "yaml" and folder:
        logger.warning("Only --folder flag will be considered")

    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    if not all:
        document = papis.api.pick_doc(documents)
        if not document:
            return 0
        documents = [document]


    ret_string = run(
        documents,
        to_format=format,
    )

    if ret_string is not None:
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
                    outdir, document.get_main_folder_name()
                )
            shutil.copytree(folder, outdir)
        elif file:
            logger.info("Exporting file")
            files = document.get_files()
            assert(isinstance(files, list))
            if not files:
                logger.error('No files found for doc in {0}'.format(
                    document.get_main_folder()
                ))
                continue
            files_to_open = [papis.api.pick(
                files,
                pick_config=dict(
                    header_filter=lambda x: x.replace(
                        document.get_main_folder(), ""
                    )
                )
            )]
            files_to_copy = list(filter(lambda x: x, files_to_open))
            for file_to_open in files_to_copy:

                if out is not None and len(files_to_open) == 1:
                    out_file = out
                else:
                    out_file = os.path.basename(file_to_open)

                logger.info("copy {0} to {1}".format(
                    file_to_open,
                    out_file
                ))
                shutil.copyfile(
                    file_to_open,
                    out_file
                )
