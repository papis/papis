"""This command will try its best to find a source in the internet for the
document at hand.

Of course if the document has an url key in its info file, it will use this url
to open it in a browser.  Also if it has a doc_url key, or a doi, it will try
to compose urls out of these to open it.

If none of the above work, then it will try to use a search engine with the
document's information (using the ``browse-query-format``).  You can select
wich search engine you want to use using the ``search-engine`` setting.

Cli
^^^
.. click:: papis.commands.browse:cli
    :prog: papis browse
"""
import papis
import papis.utils
import papis.config
from papis.api import status
import papis.cli
import papis.api
import click
import papis.database


def run(document):
    """Open document's url in a browser"""
    papis.document.open_in_browser(document)
    return status.success


@click.command()
@click.help_option('--help', '-h')
@papis.cli.query_option()
@click.option(
    '-k', '--key', default='',
    help='Use the value of the document\'s key to open in the browser, e.g.'
         'doi, url, doc_url ...'
)
def cli(query, key):
    """Open document's url in a browser"""
    documents = papis.database.get().query(query)
    document = papis.api.pick_doc(documents)
    if len(key):
        papis.config.set('browse-key', key)
    if not document:
        return status.file_not_found
    return run(document)
