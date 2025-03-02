# See https://github.com/xlcnd/isbnlib for details
from typing import Dict, Any, List, Optional

import click
from isbnlib.registry import services as isbn_services

import papis.config
import papis.document
import papis.importer
import papis.logging

logger = papis.logging.get_logger(__name__)

ISBN_SERVICE_NAMES = list(isbn_services)


def get_data(query: str = "",
             service: Optional[str] = None) -> List[Dict[str, Any]]:
    logger.debug("Trying to retrieve ISBN from query: '%s'.", query)

    if service is None:
        service = papis.config.get("isbn-service")

    if service not in ISBN_SERVICE_NAMES:
        logger.error("ISBN service '%s' is not known. Available services: '%s'.",
                     service, "', '".join(ISBN_SERVICE_NAMES))
        return []

    import isbnlib
    isbn = isbnlib.isbn_from_words(query)
    data = isbnlib.meta(isbn, service=service)
    if isinstance(data, dict):
        return [data_to_papis(data)]
    else:
        logger.error("Could not retrieve ISBN data.")
        return []


def data_to_papis(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert data from isbnlib into Papis formatted data.

    :param data: Dictionary with data
    :returns: Dictionary with Papis key names
    """
    cls = papis.document.KeyConversionPair
    key_conversion = [
        cls("authors", [{
            "key": "author_list",
            "action": papis.document.split_authors_name
        }]),
        cls("isbn-13", [
            {"key": "isbn", "action": None},
            {"key": "isbn-13", "action": None},
        ]),
        cls("language", [
            {"key": "language", "action": lambda x: x if x else "en"}
        ])
        ]

    data = {k.lower(): data[k] for k in data}
    result = papis.document.keyconversion_to_data(
        key_conversion, data, keep_unknown_keys=True)

    # NOTE: 'isbnlib' does not give a type at all, so we can't know if this is
    # a proceeding or any other book-like format. Also, 'isbnlib' always uses
    # the 'book' type when converting to BibTeX, so we'll do the same.
    result["type"] = "book"

    return result


@click.command("isbn")
@click.pass_context
@click.help_option("--help", "-h")
@click.option("--query", "-q", default=None)
@click.option("--service", "-s",
              default=ISBN_SERVICE_NAMES[0],
              type=click.Choice(ISBN_SERVICE_NAMES))
def explorer(ctx: click.core.Context, query: str, service: str) -> None:
    """
    Look for documents using `isbnlib <https://isbnlib.readthedocs.io/en/latest/>`__.

    For example, to look for a document with the author "Albert Einstein" and
    open it with Firefox, you can call

    .. code:: sh

        papis explore \\
            isbn -q 'Albert einstein' \\
            pick \\
            cmd 'firefox {doc[url]}'
    """
    logger.info("Looking up ISBN documents...")

    data = get_data(query=query, service=service)
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj["documents"] += docs

    logger.info("Found %d documents.", len(docs))


class Importer(papis.importer.Importer):

    """Importer for ISBN identifiers through isbnlib"""

    def __init__(self, uri: str) -> None:
        super().__init__(name="isbn", uri=uri)

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        import isbnlib
        if isbnlib.notisbn(uri):
            return None
        return Importer(uri=uri)

    def fetch_data(self) -> None:
        import isbnlib
        try:
            data = get_data(self.uri)
        except isbnlib.ISBNLibException:
            pass
        else:
            if data:
                self.ctx.data = data_to_papis(data[0])
