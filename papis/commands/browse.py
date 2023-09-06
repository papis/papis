"""
This command will try its best to find a source in the internet for the
document at hand.

If the document has an URL key in its ``info.yaml`` file, it will use this URL
to open it in a browser.  Also if it has a ``doc_url`` key, or a DOI, it will try
to compose URLs out of these to open it.

If none of the above work, then it will try to use a search engine with the
document's information (using the :ref:`config-settings-browse-query-format`
configuration option).  You can select which search engine you want to use
with the :ref:`config-settings-search-engine` setting.

Examples
^^^^^^^^

By default, it will use the configuration option :ref:`config-settings-browse-key`
to try and form an URL to browse. You can bypass this option using the ``-k``
flag issuing the command

.. code:: sh

    papis browse -k doi einstein

This will form an URL through the DOI of the document. Similarly,

.. code:: sh

    papis browse -k isbn

will form an URL through the ISBN of the document using
`isbnsearch.org <https://isbnsearch.org/>`__. It can also use

.. code:: sh

    papis browse -k ads

to form an URL using the great `ADS service <https://ui.adsabs.harvard.edu/>`__
and there you can check for similar papers, citations, references and much more.
Please note that for this to work the document should have a DOI attached to it.
Using

.. code:: sh

    papis browse -k whatever

will consider the key ``whatever`` from the document to be a valid URL,
assuming at this point that you'll know what you're doing. Finally, the default

.. code:: sh

    papis browse -k search-engine

will do a ``search-engine`` search with the data of your paper and hopefully
you'll find it there.

Command-line Interface
^^^^^^^^^^^^^^^^^^^^^^

.. click:: papis.commands.browse:cli
    :prog: papis browse
"""

from typing import Optional, Tuple

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
        if "auto" == key:
            if document["url"]:
                key = "url"
            elif document["doi"]:
                key = "doi"
            elif document["isbn"]:
                key = "isbn"

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
                document,
                default="{} {}".format(document["author"], document["title"]))
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
@papis.cli.bool_flag(
    "-n", "--print", "_print",
    help="Just print out the url, do not open it with browser")
@papis.cli.all_option()
@papis.cli.doc_folder_option()
def cli(query: str,
        key: str,
        _all: bool,
        _print: bool,
        doc_folder: Tuple[str, ...],
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
