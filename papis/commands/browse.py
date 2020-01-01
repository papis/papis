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


logger = logging.getLogger('browse')


def run(document):
    """Browse document's url whenever possible.

    :document: Document object
    :returns: Returns the url that is composed from the document
    :rtype:  str

    """
    global logger
    url = None
    key = papis.config.get("browse-key")

    if document.has(key):
        if "doi" == key:
            url = 'https://doi.org/{}'.format(document['doi'])
        elif "isbn" == key:
            url = 'https://isbnsearch.org/isbn/{}'.format(document['isbn'])
        else:
            url = document[key]

    if url is None or key == 'search-engine':
        params = {
            'q': papis.utils.format_doc(
                papis.config.get('browse-query-format'),
                document
            )
        }
        url = papis.config.get('search-engine') + '/?' + urlencode(params)

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
def cli(query, key, _all, sort_field, sort_reverse):
    """Open document's url in a browser"""
    documents = papis.database.get().query(query)
    logger = logging.getLogger('cli:browse')

    if len(documents) == 0:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return 0

    if not _all:
        document = papis.pick.pick_doc(documents)
        if not document:
            return
        documents = [document]

    if sort_field:
        documents = papis.document.sort(documents, sort_field, sort_reverse)

    if len(key):
        papis.config.set('browse-key', key)

    for document in documents:
        run(document)
