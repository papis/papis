"""
This command checks for several attributes in every document.

For example if you want to check that every document of your library has valid
files related to it you can just do

::

    papis check --key files

this will check that every info file has the key files and that every file
listed exists.

You can also define more complicated ones, e.g., if you want to check that
every document has files, a valid author and title you would just hit

::

    papis check --key files --key author --key title
"""
import papis.api
import papis.config
import papis.cli
import click
import logging


def run(keys, documents):
    result = []
    for document in documents:
        for key in keys:
            if key not in document.keys():
                result.append(
                    dict(doc=document, key=key, msg='not defined')
                )
            elif not document[key] and document[key] is not False:
                result.append(
                    dict(doc=document, key=key, msg='ill defined')
                )
            elif key == 'files':
                if not document.check_files():
                    result.append(
                        dict(doc=document, key=key, msg='problem with files')
                    )
    return result



@click.command()
@click.help_option('--help', '-h')
@papis.cli.query_option()
@click.option(
    "--key", "-k",
    help="Space separated fields to check against",
    type=str,
    multiple=True,
    default=lambda: eval(papis.config.get('check-keys'))
)
def cli(query, key):
    """Check document from a given library"""
    documents = papis.database.get().query(query)
    logger = logging.getLogger('cli:check')
    logger.debug(key)
    troubled_docs = run(key, documents)
    for doc in troubled_docs:
        print(
            "{d[key]} - {d[msg]} - {folder}".format(
                d=doc, folder=doc['doc'].get_main_folder()
            )
        )

    if not len(troubled_docs) == 0:
        print("Errors were detected, please fix the info files")
    else:
        print("No errors detected")
