"""This command will try its best to find a source in the internet for the
document at hand.

Of course if the document has an url key in its info file, it will use this url
to open it in a browser.  Also if it has a doc_url key, or a doi, it will try
to compose urls out of these to open it.

If none of the above work, then it will try to use a search engine with the
document's information (using the ``browse-query-format``).  You can select
which search engine you want to use using the ``search-engine`` setting.

It uses the configuration option ``browse-key`` to form an url
according to which key is given in the document. You can bypass this option
using the `-k` flag issuing the command.

::

    papis browse -k doi einstein

This will form an url through the DOI of the document.

::

    papis browse -k isbn

This will form an url through the ISBN of the document
using isbnsearch.org.

::

    papis browse -k ads

This will form an url using the gread ADS service and there you can check
for similar papers, citations, references and much more.
Please note that for this to work the document should have a DOI
attached to it.

::

    papis browse -k whatever

This will consider the key ``whatever`` of the document
to be a valid url, I guess at this point you'll know what you're doing.

::

    papis browse -k search-engine

This is the default, it will do a search-engine search with the data of your
paper and hopefully you'll find it.

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.browse:cli
    :prog: papis browse
"""

from typing import Optional

import click

import papis
import papis.utils
import papis.config
import papis.cli
import papis.pick
import papis.database
import papis.strings
import papis.document
import papis.logging

logger = papis.logging.get_logger(__name__)


def run(document: papis.document.Document,
        browse: bool = True) -> Optional[str]:
    """Browse document's url whenever possible and returns the url

    :document: Document object

    """
    url = None
    key = papis.config.getstring("browse-key")

    try:
        if "doi" == key:
            url = "https://doi.org/{}".format(document["doi"])
        elif "ads" == key:
            url = ("https://ui.adsabs.harvard.edu/abs/%22{}%22"
                   .format(document["doi"]))
        elif "isbn" == key:
            url = "https://isbnsearch.org/isbn/{}".format(document["isbn"])
        elif key != "search-engine":
            url = document[key]
    except KeyError as exc:
        logger.error("Failed to construct URL for key '%s'.", key, exc_info=exc)

    if not url or key == "search-engine":
        import urllib.parse
        params = {
            "q": papis.format.format(
                papis.config.getstring("browse-query-format"),
                document)
        }
        url = (papis.config.getstring("search-engine")
               + "/?"
               + urllib.parse.urlencode(params))

    if browse:
        logger.info("Opening URL '%s'.", url)
        papis.utils.general_open(url, "browser", wait=False)
    else:
        click.echo(url)

    return url


@click.command("browse")
@click.help_option("--help", "-h")
@papis.cli.query_argument()
@papis.cli.sort_option()
@click.option("-k", "--key", default="",
              help="Use the value of the document's key to open in"
                   " the browser, e.g. doi, url, doc_url ...")
@click.option("-n", "--print", "_print", default=False, is_flag=True,
              help="Just print out the url, do not open it with browser")
@papis.cli.all_option()
@papis.cli.doc_folder_option()
def cli(query: str,
        key: str,
        _all: bool,
        _print: bool,
        doc_folder: str,
        sort_field: Optional[str],
        sort_reverse: bool) -> None:
    """Open document's url in a browser"""
    documents = papis.cli.handle_doc_folder_query_all_sort(query,
                                                           doc_folder,
                                                           sort_field,
                                                           sort_reverse,
                                                           _all)
    if not documents:
        logger.warning(papis.strings.no_documents_retrieved_message)
        return

    if key:
        papis.config.set("browse-key", key)

    logger.info("Using key '%s'.", papis.config.get("browse-key"))

    for document in documents:
        run(document, browse=not _print)
