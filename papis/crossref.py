import os
import re
from typing import Any

import click
import doi

import papis.config
import papis.document
import papis.downloaders.base
import papis.filetype
import papis.importer
import papis.logging
import papis.pick

logger = papis.logging.get_logger(__name__)

KeyConversionPair = papis.document.KeyConversionPair

# NOTE: the API JSON format is maintained at
#   https://github.com/CrossRef/rest-api-doc/blob/master/api_format.md

#: Filters used to narrow Crossref works queries. The official list of filters
#: can be found in the
#: `REST API documentation <https://github.com/CrossRef/rest-api-doc#filter-names>`__.
CROSSREF_FILTER_NAMES = frozenset([
    "has-funder", "funder", "location", "prefix", "member", "from-index-date",
    "until-index-date", "from-deposit-date", "until-deposit-date",
    "from-update-date", "until-update-date", "from-created-date",
    "until-created-date", "from-pub-date", "until-pub-date",
    "from-online-pub-date", "until-online-pub-date", "from-print-pub-date",
    "until-print-pub-date", "from-posted-date", "until-posted-date",
    "from-accepted-date", "until-accepted-date", "has-license", "license-url",
    "license-version", "license-delay", "has-full-text", "full-text-version",
    "full-text-type", "full-text-application", "has-references",
    "reference-visibility", "has-archive", "archive", "has-orcid",
    "has-authenticated-orcid", "orcid", "issn", "isbn", "type", "directory",
    "doi", "updates", "is-update", "has-update-policy", "container-title",
    "category-name", "type", "type-name", "award-number", "award-funder",
    "has-assertion", "assertion-group", "assertion", "has-affiliation",
    "alternative-id", "article-number", "has-abstract",
    "has-clinical-trial-number", "content-domain", "has-content-domain",
    "has-domain-restriction", "has-relation", "relation-type",
    "relation-object",
])

#: Document types accepted by the Crossref API. The official list can be found
#: in the `REST API documentation <https://api.crossref.org/types>`__.
CROSSREF_TYPES = frozenset([
    "book-section", "monograph", "report-component", "report", "peer-review",
    "book-track", "journal-article", "book-part", "other", "book",
    "journal-volume", "book-set", "reference-entry", "proceedings-article",
    "journal", "component", "book-chapter", "proceedings-series",
    "report-series", "proceedings", "database", "standard", "reference-book",
    "posted-content", "journal-issue", "dissertation", "grant", "dataset",
    "book-series", "edited-book",
])

#: Fields by which Crossref queries can be sorted by. The official list can be
#: found in the
#: `REST API documentation <https://github.com/CrossRef/rest-api-doc#sorting>`__.
CROSSREF_SORT_VALUES = frozenset([
    "relevance", "score", "updated", "deposited", "indexed", "published",
    "published-print", "published-online", "issued", "is-referenced-by-count",
    "references-count",
])

#: Sorting order. The official list can be found in the
#: `REST API documentation <https://github.com/CrossRef/rest-api-doc#sorting>`__.
CROSSREF_ORDER_VALUES = frozenset(["asc", "desc"])

#: A mapping of Crossref types (see :data:`CROSSREF_TYPES`) to BibTeX types. This
#: mapping is not official in any way and is just used by Papis.
CROSSREF_TO_BIBTEX_CONVERTER = {
    # NOTE: keep order the same as `CROSSREF_TYPES`, which is the order in the
    # Crossref documentation, for easy comparison.
    "book-section": "inbook",
    "monograph": "book",
    "report-component": "incollection",
    "report": "report",
    "peer-review": "article",
    "book-track": "inbook",
    "journal-article": "article",
    "book-part": "inbook",
    "other": "misc",
    "book": "book",
    "journal-volume": "collection",
    "book-set": "mvcollection",
    "reference-entry": "inreference",
    "proceedings-article": "inproceedings",
    "journal": "collection",
    "component": "incollection",
    "book-chapter": "inbook",
    "proceedings-series": "mvproceedings",
    "report-series": "mvcollection",
    "proceedings": "proceedings",
    "database": "misc",
    "standard": "report",
    "reference-book": "reference",
    "posted-content": "online",
    "journal-issue": "collection",
    "dissertation": "thesis",
    "grant": "misc",
    "dataset": "dataset",
    "book-series": "incollection",
    "edited-book": "book",
}

# NOTE: fields checked against the official API format
# https://github.com/CrossRef/rest-api-doc/blob/583a8dbad0a063da4aa5ec319df33130a26ef650/api_format.md
key_conversion = [
    KeyConversionPair("DOI", [{"key": "doi", "action": None}]),
    KeyConversionPair("URL", [{"key": "url", "action": None}]),
    KeyConversionPair("author", [{
        "key": "author_list",
        "action": lambda authors: [
            {k: a.get(k) for k in ["given", "family", "affiliation"]}
            for a in authors
        ],
    }]),
    KeyConversionPair("container-title", [
        {"key": "journal", "action": lambda x: x[0]}]),
    KeyConversionPair("issue", [papis.document.EmptyKeyConversion]),
    # "issued": {"key": "",},
    KeyConversionPair("language", [papis.document.EmptyKeyConversion]),
    KeyConversionPair("abstract", [papis.document.EmptyKeyConversion]),
    KeyConversionPair("ISBN", [{
        "key": "isbn",
        "action": lambda x: x[0] if isinstance(x, list) else x
    }]),
    KeyConversionPair("isbn-type", [{
        "key": "isbn",
        "action": lambda x: next(i for i in x if i["type"] == "electronic")["value"]
    }]),
    KeyConversionPair("page", [{
        "key": "pages",
        "action": lambda p: re.sub(r"(-[^-])", r"-\1", p),
    }]),
    KeyConversionPair("link", [{
        "key": str(papis.config.getstring("doc-url-key-name")),
        "action": lambda x: _crossref_link(x)  # noqa: PLW0108
    }]),
    KeyConversionPair("issued", [
        {"key": "year", "action": lambda x: _crossref_date_parts(x, 0)},
        {"key": "month", "action": lambda x: _crossref_date_parts(x, 1)}
    ]),
    KeyConversionPair("published-online", [
        {"key": "year", "action": lambda x: _crossref_date_parts(x, 0)},
        {"key": "month", "action": lambda x: _crossref_date_parts(x, 1)}
    ]),
    KeyConversionPair("published-print", [
        {"key": "year", "action": lambda x: _crossref_date_parts(x, 0)},
        {"key": "month", "action": lambda x: _crossref_date_parts(x, 1)}
    ]),
    KeyConversionPair("publisher", [papis.document.EmptyKeyConversion]),
    KeyConversionPair("reference", [{
        "key": "citations",
        "action": lambda cs: [
            {key.lower(): c[key]
                for key in set(c) - {"key", "doi-asserted-by"}}
            for c in cs
        ]
    }]),
    KeyConversionPair("title", [
        {"key": None, "action": lambda t: " ".join(t)}]),  # noqa: PLW0108
    KeyConversionPair("type", [
        {"key": None, "action": lambda t: CROSSREF_TO_BIBTEX_CONVERTER[t]}]),
    KeyConversionPair("volume", [papis.document.EmptyKeyConversion]),
    KeyConversionPair("event", [  # Conferences
        {"key": "venue", "action": lambda x: x["location"]},
        {"key": "booktitle", "action": lambda x: x["name"]},
        {"key": "year",
         "action": (lambda x:
                    _crossref_date_parts(x["start"], 0) if "start" in x else None)},
        {"key": "month",
         "action": (lambda x:
                    _crossref_date_parts(x["start"], 1) if "start" in x else None)},
    ]),
]  # List[papis.document.KeyConversionPair]


def _crossref_date_parts(entry: dict[str, Any], i: int = 0) -> int | None:
    date_parts = entry.get("date-parts")
    if date_parts is None:
        return date_parts

    assert len(date_parts) == 1
    parts, = date_parts

    # NOTE: dates can also be partial, where only the year is required
    if not (0 <= i < len(parts)):
        return None

    return int(parts[i])


def _crossref_link(entry: list[dict[str, str]]) -> str | None:
    if len(entry) == 1:
        return entry[0]["URL"]

    links = [
        # NOTE: using the 'similarity-checking' label here is just a heuristic,
        # since that seemed to be the better choice in some examples
        resource.get("URL") for resource in entry
        if resource.get("intended-application") == "similarity-checking"]

    return links[0] if links else None


def crossref_data_to_papis_data(data: dict[str, Any]) -> dict[str, Any]:
    new_data = papis.document.keyconversion_to_data(key_conversion, data)

    # ensure that author_list and author are consistent
    new_data["author"] = papis.document.author_list_to_author(new_data)

    # special cleanup for APS journals
    # xref: https://github.com/papis/papis/issues/1019
    #       https://github.com/JabRef/jabref/issues/7019
    #       https://journals.aps.org/pra/articleid
    if "pages" not in new_data:
        article_number = data.get("article-number", None)
        if article_number:
            # FIXME: add nicer DOI parsing (probably in `python-doi`)
            # determine from DOI if the journal in question is an APS journal.
            is_aps = False
            doi = new_data.get("doi", "")
            if "/" in doi:
                prefix, _ = doi.split("/", maxsplit=1)
                if "." in prefix:
                    _, journal_id = prefix.split(".", maxsplit=1)
                    is_aps = journal_id == "1103"

            if is_aps:
                new_data["pages"] = article_number

    return new_data


def _get_crossref_works(**kwargs: Any) -> dict[str, Any] | list[dict[str, Any]]:
    import habanero

    from papis import PAPIS_USER_AGENT

    cr = habanero.Crossref(
        # TODO: Check if this is an acceptable value for the field. From the
        # documentation, `mailto` is just meant to act as a contact point?
        mailto="https://github.com/papis/papis/issues",
        ua_string=PAPIS_USER_AGENT,
    )

    return cr.works(**kwargs)  # type: ignore[no-any-return]


def get_data(
        query: str = "",
        author: str = "",
        title: str = "",
        dois: list[str] | None = None,
        max_results: int = 0,
        filters: dict[str, Any] | None = None,
        sort: str = "score",
        order: str = "desc") -> list[dict[str, Any]]:
    assert sort in CROSSREF_SORT_VALUES, "Sort value not valid"
    assert order in CROSSREF_ORDER_VALUES, "Order value not valid"

    if dois is None:
        dois = []

    if filters is None:
        filters = {}

    if filters:
        unknown_filters = set(filters) - CROSSREF_FILTER_NAMES
        if unknown_filters:
            raise ValueError(
                "Unknown filters '{}'. Filter keys must be one of '{}'"
                .format("', '".join(unknown_filters),
                        "', '".join(CROSSREF_FILTER_NAMES))
            )
    data = {
        "query": query,
        "query_author": author,
        "ids": dois,
        "query_title": title,
        "limit": max_results
        }

    kwargs = {key: data[key] for key in data if data[key]}
    if not dois:
        kwargs.update({"sort": sort, "order": order})
    try:
        results = _get_crossref_works(filter=filters, **kwargs)
    except Exception as exc:
        logger.error("Error getting works from Crossref.", exc_info=exc)
        return []

    if isinstance(results, list):
        docs = [d["message"] for d in results]
    elif isinstance(results, dict):
        if "message" not in results:
            logger.error("Error retrieving data from Crossref: incorrect message.")
            return []
        message = results["message"]
        if "items" in message:
            docs = message["items"]
        else:
            docs = [message]
    else:
        logger.error("Error retrieving data from Crossref: incorrect message.")
        return []

    logger.debug("Retrieved %s documents.", len(docs))
    return [crossref_data_to_papis_data(d) for d in docs]


def doi_to_data(doi_string: str) -> dict[str, Any]:
    """Search through Crossref and get the document metadata.

    :param doi_string: DOI or an url that contains a DOI.
    :returns: dictionary containing the data.
    :raises ValueError: if no data could be retrieved for the DOI.
    """
    doi_string = doi.get_clean_doi(doi_string)
    results = get_data(dois=[doi_string])
    if results:
        return results[0]

    raise ValueError(
        f"Could not retrieve data for DOI '{doi_string}' from Crossref")


@click.command("crossref")
@click.pass_context
@click.help_option("--help", "-h")
@click.option("--query", "-q", help="General query.", default="")
@click.option("--author", "-a", help="Author of the query.", default="")
@click.option("--title", "-t", help="Title of the query.", default="")
@click.option(
    "--max", "-m", "_ma", help="Maximum number of results.", default=20)
@click.option(
    "--filter", "-f", "_filters", help="Filters to apply.", default=(),
    type=(click.Choice(list(_filter_names)), str),
    multiple=True)
@click.option(
    "--order", "-o", help="Order of appearance according to sorting.",
    default="desc", type=click.Choice(list(_order_values)), show_default=True)
@click.option(
    "--sort", "-s", help="Sorting parameter.", default="score",
    type=click.Choice(list(_sort_values)), show_default=True)
def explorer(
        ctx: click.core.Context,
        query: str,
        author: str,
        title: str,
        _ma: int,
        _filters: list[tuple[str, str]],
        sort: str,
        order: str) -> None:
    """
    Look for documents on `Crossref <https://www.crossref.org/>`__.

    For example, to look for a document with the author "Albert Einstein" and
    export it to a BibTeX file, you can call:

    .. code:: sh

        papis explore \\
            crossref -a 'Albert einstein' \\
            pick \\
            export --format bibtex lib.bib
    """
    logger.info("Looking up Crossref documents...")

    data = get_data(
        query=query,
        author=author,
        title=title,
        max_results=_ma,
        filters=dict(_filters),
        sort=sort,
        order=order)
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj["documents"] += docs

    logger.info("Found %s documents.", len(docs))


class DoiFromPdfImporter(papis.importer.Importer):

    """Importer parsing a DOI from a PDF file and importing data from Crossref"""

    def __init__(self, uri: str) -> None:
        """The uri should be a filepath"""
        super().__init__(name="pdf2doi", uri=uri)
        self._doi: str | None = None

    @classmethod
    def match(cls, uri: str) -> papis.importer.Importer | None:
        """The uri should be a filepath"""
        filepath = uri
        if (
                os.path.isdir(filepath)
                or not os.path.exists(filepath)
                or not papis.filetype.get_document_extension(filepath) == "pdf"
                ):
            return None

        importer = DoiFromPdfImporter(filepath)
        return importer if importer.doi else None

    @property
    def doi(self) -> str | None:
        if self._doi is None:
            self._doi = doi.pdf_to_doi(self.uri, maxlines=2000)
            self._doi = "" if self._doi is None else self._doi

            if self._doi:
                self.logger.info("Parsed DOI '%s' from file: '%s'.",
                                 self._doi, self.uri)
                self.logger.warning(
                    "There is no guarantee that this DOI is the correct one!")
            else:
                self.logger.debug("No DOI found in document: '%s'", self.uri)

        return self._doi

    def fetch(self) -> None:
        if self.doi:
            importer = Importer(uri=self.doi)
            importer.fetch()
            self.ctx = importer.ctx


class Importer(papis.importer.Importer):

    """Importer getting files and data from a DOI through Crossref"""

    def __init__(self, uri: str) -> None:
        super().__init__(name="doi", uri=uri)

    @classmethod
    def match(cls, uri: str) -> papis.importer.Importer | None:
        try:
            doi.validate_doi(uri)
        except ValueError:
            return None
        else:
            return Importer(uri=uri)

    @classmethod
    def match_data(cls, data: dict[str, Any]) -> papis.importer.Importer | None:
        if "doi" in data:
            return Importer(uri=data["doi"])

        return None

    def fetch_data(self) -> None:
        data = papis.crossref.get_data(dois=[self.uri])
        if data:
            self.ctx.data = data[0]

    def fetch_files(self) -> None:
        if not self.ctx.data:
            return

        doc_url = self.ctx.data.get(
            papis.config.getstring("doc-url-key-name"),
            None)

        if doc_url is None:
            return

        self.logger.info("Trying to download document from '%s'.", doc_url)

        from papis.downloaders import download_document
        filename = download_document(doc_url)
        if filename is not None:
            self.ctx.files.append(filename)


class FromCrossrefImporter(papis.importer.Importer):

    """Importer that gets data from querying Crossref"""

    def __init__(self, uri: str) -> None:
        super().__init__(uri=uri, name="crossref")

    @classmethod
    def match(cls, uri: str) -> papis.importer.Importer | None:
        # There is no way to check if it matches
        return None

    @classmethod
    def match_data(cls, data: dict[str, Any]) -> papis.importer.Importer | None:
        if "title" in data:
            return FromCrossrefImporter(uri=data["title"])

        return None

    def fetch_data(self) -> None:
        self.logger.info("Querying Crossref with '%s'.", self.uri)
        docs = [
            papis.document.from_data(d)
            for d in get_data(query=self.uri)]

        if not docs:
            return

        self.logger.warning(
            "Crossref query '%s' returned %d results. Picking the first one!",
            self.uri, len(docs))

        doc = docs[0]
        importer = Importer(uri=doc["doi"])
        importer.fetch()
        self.ctx.data = importer.ctx.data.copy()


class Downloader(papis.downloaders.Downloader):
    """Retrieve documents by DOI from `Crossref <https://www.crossref.org>`__"""

    def __init__(self, uri: str) -> None:
        super().__init__(uri=uri, name="doi")
        self._doi: str | None = None

    @classmethod
    def match(cls, uri: str) -> papis.downloaders.Downloader | None:
        down = Downloader(uri)
        return down if down.doi else None

    @property
    def doi(self) -> str | None:
        if self._doi is None:
            self._doi = doi.find_doi_in_text(self.uri)
            self._doi = "" if self._doi is None else self._doi

        return self._doi

    def fetch_data(self) -> None:
        self.fetch()

    def fetch(self) -> None:
        if not self.doi:
            return

        importer = Importer(uri=self.doi)
        importer.fetch()
        self.ctx = importer.ctx
