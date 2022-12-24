# See https://github.com/xlcnd/isbnlib for details
import logging
from typing import Dict, Any, List, Optional

import click

import papis.document
import papis.importer

logger = logging.getLogger("papis:isbnlib")


def get_data(query: str = "",
             service: str = "openl") -> List[Dict[str, Any]]:
    logger.debug("Trying to retrieve isbn from query: '%s'", query)

    import isbnlib
    results = []  # type: List[Dict[str, Any]]
    isbn = isbnlib.isbn_from_words(query)
    data = isbnlib.meta(isbn, service=service)
    if data is None:
        return results
    else:
        assert isinstance(data, dict)
        results.append(data_to_papis(data))
        return results


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
              type=click.Choice(["wcat", "goob", "openl"]))
def explorer(ctx: click.core.Context, query: str, service: str) -> None:
    """
    Look for documents using isbnlib

    Examples of its usage are

    papis explore isbn -q 'Albert einstein' pick cmd 'firefox {doc[url]}'

    """
    logger = logging.getLogger("explore:isbn")
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
