import re
import os
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

import doi
import click

import papis.config
import papis.pick
import papis.filetype
import papis.document
import papis.importer
import papis.downloaders.base
import papis.logging

if TYPE_CHECKING:
    import habanero

logger = papis.logging.get_logger(__name__)

KeyConversionPair = papis.document.KeyConversionPair

# NOTE: the API JSON format is maintained at
#   https://github.com/CrossRef/rest-api-doc/blob/master/api_format.md

_filter_names = frozenset([
    "has_funder", "funder", "location", "prefix", "member", "from_index_date",
    "until_index_date", "from_deposit_date", "until_deposit_date",
    "from_update_date", "until_update_date", "from_created_date",
    "until_created_date", "from_pub_date", "until_pub_date",
    "from_online_pub_date", "until_online_pub_date", "from_print_pub_date",
    "until_print_pub_date", "from_posted_date", "until_posted_date",
    "from_accepted_date", "until_accepted_date", "has_license",
    "license_url", "license_version", "license_delay",
    "has_full_text", "full_text_version", "full_text_type",
    "full_text_application", "has_references", "has_archive",
    "archive", "has_orcid", "has_authenticated_orcid",
    "orcid", "issn", "type", "directory", "doi", "updates", "is_update",
    "has_update_policy", "container_title", "category_name", "type",
    "type_name", "award_number", "award_funder", "has_assertion",
    "assertion_group", "assertion", "has_affiliation", "alternative_id",
    "article_number", "has_abstract", "has_clinical_trial_number",
    "content_domain", "has_content_domain", "has_crossmark_restriction",
    "has_relation", "relation_type", "relation_object", "relation_object_type",
    "public_references", "publisher_name", "affiliation",
])

_types_values = frozenset([
    "book-section", "monograph", "report", "peer-review", "book-track",
    "journal-article", "book-part", "other", "book", "journal-volume",
    "book-set", "reference-entry", "proceedings-article", "journal",
    "component", "book-chapter", "proceedings-series", "report-series",
    "proceedings", "standard", "reference-book", "posted-content",
    "journal-issue", "dissertation", "dataset", "book-series", "edited-book",
    "standard-series",
])

_sort_values = frozenset([
    "relevance", "score", "updated", "deposited", "indexed", "published",
    "published-print", "published-online", "issued", "is-referenced-by-count",
    "references-count",
])


_order_values = frozenset(["asc", "desc"])


type_converter = {
    "book": "book",
    "book-chapter": "inbook",
    "book-part": "inbook",
    "book-section": "inbook",
    "book-series": "incollection",
    "book-set": "incollection",
    "book-track": "inbook",
    "dataset": "misc",
    "dissertation": "phdthesis",
    "edited-book": "book",
    "journal-article": "article",
    "journal-issue": "misc",
    "journal-volume": "article",
    "monograph": "monograph",
    "other": "misc",
    "peer-review": "article",
    "posted-content": "misc",
    "proceedings-article": "inproceedings",
    "proceedings": "inproceedings",
    "proceedings-series": "inproceedings",
    "reference-book": "book",
    "report": "report",
    "report-series": "inproceedings",
    "standard-series": "incollection",
    "standard": "techreport",
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
        "key": str(papis.config.get("doc-url-key-name")),
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
        {"key": None, "action": lambda t: type_converter[t]}]),
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


def _crossref_date_parts(entry: Dict[str, Any],
                         i: int = 0) -> Optional[int]:
    date_parts = entry.get("date-parts")
    if date_parts is None:
        return date_parts

    assert len(date_parts) == 1
    parts, = date_parts

    # NOTE: dates can also be partial, where only the year is required
    if not (0 <= i < len(parts)):
        return None

    return int(parts[i])


def _crossref_link(entry: List[Dict[str, str]]) -> Optional[str]:
    if len(entry) == 1:
        return entry[0]["URL"]

    links = [
        # NOTE: using the 'similarity-checking' label here is just a heuristic,
        # since that seemed to be the better choice in some examples
        resource.get("URL") for resource in entry
        if resource.get("intended-application") == "similarity-checking"]

    return links[0] if links else None


def crossref_data_to_papis_data(data: Dict[str, Any]) -> Dict[str, Any]:
    new_data = papis.document.keyconversion_to_data(key_conversion, data)
    new_data["author"] = papis.document.author_list_to_author(new_data)
    return new_data


def _get_crossref_works(**kwargs: Any) -> "habanero.request_class.Request":
    import habanero
    cr = habanero.Crossref()
    return cr.works(**kwargs)


def get_data(
        query: str = "",
        author: str = "",
        title: str = "",
        dois: Optional[List[str]] = None,
        max_results: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        sort: str = "score",
        order: str = "desc") -> List[Dict[str, Any]]:
    assert sort in _sort_values, "Sort value not valid"
    assert order in _order_values, "Sort value not valid"

    if dois is None:
        dois = []

    if filters is None:
        filters = {}

    if filters:
        unknown_filters = set(filters) - _filter_names
        if unknown_filters:
            raise ValueError(
                "Unknown filters '{}'. Filter keys must be one of '{}'"
                .format("', '".join(unknown_filters), "', '".join(_filter_names))
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


def doi_to_data(doi_string: str) -> Dict[str, Any]:
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
@click.option("--query", "-q", help="General query", default="")
@click.option("--author", "-a", help="Author of the query", default="")
@click.option("--title", "-t", help="Title of the query", default="")
@click.option(
    "--max", "-m", "_ma", help="Maximum number of results", default=20)
@click.option(
    "--filter", "-f", "_filters", help="Filters to apply", default=(),
    type=(click.Choice(list(_filter_names)), str),
    multiple=True)
@click.option(
    "--order", "-o", help="Order of appearance according to sorting",
    default="desc", type=click.Choice(list(_order_values)), show_default=True)
@click.option(
    "--sort", "-s", help="Sorting parameter", default="score",
    type=click.Choice(list(_sort_values)), show_default=True)
def explorer(
        ctx: click.core.Context,
        query: str,
        author: str,
        title: str,
        _ma: int,
        _filters: List[Tuple[str, str]],
        sort: str,
        order: str) -> None:
    """
    Look for documents on `Crossref <https://www.crossref.org/>`__.

    For example, to look for a document with the author "Albert Einstein" and
    export it to a BibTeX file, you can call

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
        self._doi: Optional[str] = None

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
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
    def doi(self) -> Optional[str]:
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
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        try:
            doi.validate_doi(uri)
        except ValueError:
            return None
        else:
            return Importer(uri=uri)

    @classmethod
    def match_data(
            cls, data: Dict[str, Any]) -> Optional[papis.importer.Importer]:
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
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        # There is no way to check if it matches
        return None

    @classmethod
    def match_data(
            cls, data: Dict[str, Any]) -> Optional[papis.importer.Importer]:
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
        self._doi: Optional[str] = None

    @classmethod
    def match(cls, uri: str) -> Optional[papis.downloaders.Downloader]:
        down = Downloader(uri)
        return down if down.doi else None

    @property
    def doi(self) -> Optional[str]:
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
