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
import papis.cli
import papis.pick
import click
import papis.database
import papis.strings
import papis.document
from urllib.parse import urlencode
import logging

from typing import Optional

logger = logging.getLogger('browse')


def run(document: papis.document.Document) -> Optional[str]:
    """Browse document's url whenever possible and returns the url

    :document: Document object

    """
    global logger
    url = None
    key = papis.config.getstring("browse-key")

    if document.has(key):
        if "doi" == key:
            url = 'https://doi.org/{}'.format(document['doi'])
        elif "isbn" == key:
            url = 'https://isbnsearch.org/isbn/{}'.format(document['isbn'])
        else:
            url = document[key]

    if url is None or key == 'search-engine':
        params = {
            'q': papis.document.format_doc(
                papis.config.getstring('browse-query-format'),
                document
            )
        }
        url = (
            papis.config.getstring('search-engine') +
            '/?' +
            urlencode(params))

    logger.info("Opening url %s:" % url)
    papis.utils.general_open(url, "browser", wait=False)
    return url


@click.command("browse")
@click.help_option('--help', '-h')
@papis.cli.query_option()
@papis.cli.sort_option()
@click.option(
    '-k', '--key', default='',
    help='Use the value of the document\'s key to open in the browser, e.g.'
         'doi, url, doc_url ...'
)
@papis.cli.all_option()
@papis.cli.doc_folder_option()
def cli(query: str,
        key: str,
        _all: bool,
        doc_folder: str,
        sort_field: Optional[str],
        sort_reverse: bool) -> None:
    """Open document's url in a browser"""

    if doc_folder:
        documents = [papis.document.from_folder(doc_folder)]
    else:
        documents = papis.database.get().query(query)

    logger = logging.getLogger('cli:browse')

    if len(documents) == 0:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    if not _all:
        documents = list(papis.pick.pick_doc(documents))
        if not documents:
            return

    if sort_field:
        documents = papis.document.sort(documents, sort_field, sort_reverse)

    if len(key):
        papis.config.set('browse-key', key)

    for document in documents:
        run(document)
