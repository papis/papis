import re
from typing import Any, Dict, List, Optional

import click

import papis.utils
import papis.config
import papis.importer
import papis.document
import papis.logging

logger = papis.logging.get_logger(__name__)

# NOTE: general API information can be found at
#   https://dblp.org/faq/How+to+use+the+dblp+search+API.html
DBLP_API_ENDPOINTS = {
    "publ": "https://dblp.org/search/publ/api",
    "author": "https://dblp.org/search/author/api",
    "venue": "https://dblp.org/search/venue/api",
}
DBLP_URL_FORMAT = "https://dblp.org/rec/{uri}.html"
DBLP_BIB_FORMAT = "https://dblp.org/rec/{uri}.bib"

DBLP_FORMATS = frozenset(["xml", "json", "jsonp"])

# NOTE: caps due to bandwidth reasons
DBLP_MAX_RESULTS = 1000
DBLP_MAX_COMPLETIONS = 1000

# https://dblp.org/faq/What+types+does+dblp+use+for+publication+entries.html
DBLP_TYPE_TO_BIBTEX = {
    "Books and Theses": "book",
    "Journal Articles": "article",
    "Conference and Workshop Papers": "inproceedings",
    "Parts in Books or Collections": "inbook",
    "Editorship": "book",
    "Reference Works": "reference",
    "Data and Artifacts": "dataset",
    "Informal or Other Publications": "report",
}

_k = papis.document.KeyConversionPair
DBLP_KEY_CONVERSION = [
    _k("title", [{"key": "title", "action": None}]),
    _k("volume", [{"key": "volume", "action": None}]),
    _k("number", [{"key": "number", "action": None}]),
    _k("pages", [{"key": "pages", "action": None}]),
    _k("year", [{"key": "year", "action": int}]),
    _k("doi", [{"key": "doi", "action": None}]),
    _k("url", [{"key": "url", "action": None}]),
    _k("type", [{"key": "type", "action": DBLP_TYPE_TO_BIBTEX.get}]),
    _k("venue", [{"key": "journal", "action": lambda x: _dblp_journal(x)}]),
    _k("authors", [{"key": "author_list", "action": lambda x: _dblp_authors(x)}]),
]


def _dblp_journal(name: str) -> Optional[str]:
    import json
    result = json.loads(search(query=f"{name}$", api="venue"))

    hits = result["result"]["hits"].get("hit")
    if hits is None or len(hits) != 1:
        return None

    journal = hits[0]["info"]["venue"]
    return str(journal) if journal else None


def _dblp_authors(entries: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [papis.document.split_author_name(author["text"])
            for author in entries["author"]]


def search(
        query: str = "",
        output_format: str = "json",
        max_results: int = 30,
        max_completions: int = 10,
        api: str = "publ",
        ) -> str:
    """Query one of the DBLP APIs.

    :param query: a DBLP compatible query string (see the
        `documentation <https://dblp.org/faq/1474589.html>`__ for details).
    :param format: format of the query response (should be one of
        ``"xml"``, ``"json"`` or ``"jsonp"``).
    :param max_results: maximum number of returned results
        (smaller than 1000).
    :param max_completions: maximum number of completions for the query
        string (considers prefix matching).
    :param api: entpoint for the DBLP API to be used (one of ``"publ"``,
        ``"author"`` or ``"venue"``).

    :result: the query response in the requested format.
    """
    if not (0 < max_results <= DBLP_MAX_RESULTS):
        raise ValueError(
            f"Cannot request more than {DBLP_MAX_RESULTS} results (got {max_results})"
            )

    if not (0 < max_completions <= DBLP_MAX_COMPLETIONS):
        raise ValueError(
            f"Cannot request more than {DBLP_MAX_COMPLETIONS} completions "
            f"(got {max_completions})")

    if output_format not in DBLP_FORMATS:
        raise ValueError(
            f"Unsupported format: '{output_format}' (expected {DBLP_FORMATS})"
            )

    url = DBLP_API_ENDPOINTS.get(api.lower())
    if url is None:
        raise ValueError(f"Unknown API endpoint '{api}'")

    with papis.utils.get_session() as session:
        response = session.get(
            url,
            params={
                "q": query,
                "format": output_format,
                "h": str(max_results),
                "f": "0",
                "c": str(max_completions),
            })

    return response.content.decode()


def get_data(query: str = "", max_results: int = 30) -> List[Dict[str, Any]]:
    import json
    response = json.loads(
        search(query=query, output_format="json", max_results=max_results)
        )
    result = response.get("result")
    hits = result["hits"].get("hit")

    if hits is None:
        logger.error("Could not retrieve results from DBLP. Error: '%s'.",
                     result["status"]["text"])
        return []

    return [papis.document.keyconversion_to_data(DBLP_KEY_CONVERSION, hit["info"])
            for hit in hits]


def is_valid_dblp_key(key: str) -> bool:
    # FIXME: Is there some documentation on the form of the keys? From a quick
    # skim, they seem to be of the form
    #   <venue type>/<venue id>/<document id>

    if not re.match(r"[^\/]+\/[^\/]+\/[^\/]+", key):
        return False

    with papis.utils.get_session() as session:
        response = session.get(DBLP_URL_FORMAT.format(uri=key))
        return response.ok


@click.command("dblp")
@click.pass_context
@click.help_option("--help", "-h")
@click.option(
    "--query", "-q",
    help="General query",
    default="")
@click.option(
    "--max", "-m", "max_results",
    help="Maximum number of results",
    default=30)
def explorer(
        ctx: click.core.Context,
        query: str,
        max_results: int) -> None:
    """
    Look for documents on `dblp.org <https://dblp.org/>`__.

    For example, to look for a document with the author "Albert Einstein" and
    export it to a BibTeX file, you can call

    .. code:: sh

        papis explore \\
            dblp -a 'Albert einstein' \\
            pick \\
            export --format bibtex lib.bib
    """
    logger.info("Looking up DBLP documents...")

    data = get_data(query=query, max_results=max_results)
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj["documents"] += docs

    logger.info("Found %d documents.", len(docs))


class Importer(papis.importer.Importer):

    """Importer for DBLP data from a key or URL."""

    def __init__(self, uri: str) -> None:
        super().__init__(name="dblp", uri=uri)

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        if re.match(r".*dblp\.org.*\.html", uri):
            return Importer(uri)
        elif is_valid_dblp_key(uri):
            return Importer(uri=DBLP_URL_FORMAT.format(uri=uri))
        else:
            return None

    def fetch_data(self) -> None:
        import papis.bibtex

        # uri: https://dblp.org/rec/conf/iccg/EncarnacaoAFFGM93.html
        # bib: https://dblp.org/rec/conf/iccg/EncarnacaoAFFGM93.bib
        if is_valid_dblp_key(self.uri):
            url = DBLP_BIB_FORMAT.format(uri=self.uri)
        else:
            url = f"{self.uri[:-5]}.bib"

        with papis.utils.get_session() as session:
            response = session.get(url)

        if not response.ok:
            logger.error("Could not get BibTeX entry for '%s'.", self.uri)
            return

        entries = papis.bibtex.bibtex_to_dict(response.content.decode())
        if not entries:
            return

        if len(entries) > 1:
            logger.warning("Found %d BibTeX entries for '%s'. Picking first one!",
                           len(entries), self.uri)

        self.ctx.data.update(entries[0])
