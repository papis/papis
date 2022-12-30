# See https://github.com/xlcnd/isbnlib for details
from typing import Dict, Any, List, Optional

import click

import papis.config
import papis.document
import papis.importer
import papis.logging

logger = papis.logging.get_logger(__name__)


def get_data(query: str = "",
             service: Optional[str] = None) -> List[Dict[str, Any]]:
    logger.debug("Trying to retrieve isbn from query: '%s'", query)

    if service is None:
        service = papis.config.get("isbn-service")

    import isbnlib.registry
    if service not in isbnlib.registry.services:
        logger.error("ISBN service '%s' is not known. Available services: '%s'.",
                     service, "', '".join(isbnlib.registry.services))
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
    Convert data from isbnlib into papis formatted data.

    :param data: Dictionary with data
    :returns: Dictionary with papis key names
    """
    _k = papis.document.KeyConversionPair
    key_conversion = [
        _k("authors", [{
            "key": "author_list",
            "action": papis.document.split_authors_name
            }]),
        _k("isbn-13", [
            {"key": "isbn", "action": None},
            {"key": "isbn-13", "action": None},
            ]),
        ]

    data = {k.lower(): data[k] for k in data}
    return papis.document.keyconversion_to_data(
        key_conversion, data, keep_unknown_keys=True)


@click.command("isbn")
@click.pass_context
@click.help_option("--help", "-h")
@click.option("--query", "-q", default=None)
@click.option("--service", "-s",
              default="goob",
              type=click.Choice(["wiki", "goob", "openl"]))
def explorer(ctx: click.core.Context, query: str, service: str) -> None:
    """
    Look for documents using isbnlib

    Examples of its usage are

    papis explore isbn -q 'Albert einstein' pick cmd 'firefox {doc[url]}'

    """
    logger.info("Looking up...")

    data = get_data(query=query, service=service)
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj["documents"] += docs

    logger.info("%d documents found", len(docs))


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

    def fetch(self) -> None:
        import isbnlib
        try:
            data = get_data(self.uri)
        except isbnlib.ISBNLibException:
            pass
        else:
            if data:
                self.ctx.data = data_to_papis(data[0])
