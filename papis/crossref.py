import re
import os
import logging
import tempfile
from typing import Set, List, Dict, Any, Optional, Tuple  # noqa: ignore

import requests
import requests.structures
import click
import doi
import habanero

import papis.config
import papis.pick
import papis.filetype
import papis.document
import papis.importer
import papis.downloaders.base

LOGGER = logging.getLogger("crossref")  # type: logging.Logger
LOGGER.debug("importing")
KeyConversionPair = papis.document.KeyConversionPair

_filter_names = set([
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
])  # type: Set[str]

_types_values = [
    "book-section", "monograph", "report", "peer-review", "book-track",
    "journal-article", "book-part", "other", "book", "journal-volume",
    "book-set", "reference-entry", "proceedings-article", "journal",
    "component", "book-chapter", "proceedings-series", "report-series",
    "proceedings", "standard", "reference-book", "posted-content",
    "journal-issue", "dissertation", "dataset", "book-series", "edited-book",
    "standard-series",
]  # type: List[str]

_sort_values = [
    "relevance", "score", "updated", "deposited", "indexed", "published",
    "published-print", "published-online", "issued", "is-referenced-by-count",
    "references-count",
]  # type: List[str]


_order_values = ['asc', 'desc']  # type: List[str]


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
}  # type: Dict[str, str]


key_conversion = [
    KeyConversionPair("DOI", [{"key": "doi", "action": None}]),
    KeyConversionPair("URL", [{"key": "url", "action": None}]),
    KeyConversionPair("author", [{
        "key": "author_list",
        "action": lambda authors: [
            {k: a.get(k) for k in ['given', 'family', 'affiliation']}
            for a in authors
        ],
    }]),
    KeyConversionPair("container-title", [
        {"key": "journal", "action": lambda x: x[0]}]),
    KeyConversionPair("issue", [papis.document.EmptyKeyConversion]),
    # "issued": {"key": "",},
    KeyConversionPair("language", [papis.document.EmptyKeyConversion]),
    KeyConversionPair("abstract", [papis.document.EmptyKeyConversion]),
    KeyConversionPair("ISBN", [{"key": "isbn", "action": None}]),
    KeyConversionPair("page", [{
        "key": "pages",
        "action": lambda p: re.sub(r"(-[^-])", r"-\1", p),
    }]),
    KeyConversionPair("link", [{
        "key": str(papis.config.get('doc-url-key-name')),
        "action": lambda x: x[1]["URL"]
    }]),
    KeyConversionPair("issued", [
        {"key": "year", "action": lambda x: x.get("date-parts")[0][0]},
        {"key": "month", "action": lambda x: x.get("date-parts")[0][1]}
    ]),
    KeyConversionPair("published-online", [
        {"key": "year", "action": lambda x: x.get("date-parts")[0][0]},
        {"key": "month", "action": lambda x: x.get("date-parts")[0][1]}
    ]),
    KeyConversionPair("published-print", [
        {"key": "year", "action": lambda x: x.get("date-parts")[0][0]},
        {"key": "month", "action": lambda x: x.get("date-parts")[0][1]}
    ]),
    KeyConversionPair("publisher", [papis.document.EmptyKeyConversion]),
    KeyConversionPair("reference", [{
        "key": "citations",
        "action": lambda cs: [
            {key.lower(): c[key]
                for key in set(c.keys()) - set(("key", "doi-asserted-by"))}
            for c in cs
        ]
    }]),
    KeyConversionPair("title", [
        {"key": None, "action": lambda t: " ".join(t)}]),
    KeyConversionPair("type", [
        {"key": None, "action": lambda t: type_converter[t]}]),
    KeyConversionPair("volume", [papis.document.EmptyKeyConversion]),
    KeyConversionPair("event", [  # Conferences
        {"key": "venue", "action": lambda x: x["location"]},
        {"key": "booktitle", "action": lambda x: x["name"]},
        {"key": "year", "action": lambda x: x['start']["date-parts"][0][0]},
        {"key": "month", "action": lambda x: x['start']["date-parts"][0][1]},
    ]),
]  # List[papis.document.KeyConversionPair]


def crossref_data_to_papis_data(data: Dict[str, Any]) -> Dict[str, Any]:
    global key_conversion
    new_data = papis.document.keyconversion_to_data(key_conversion, data)
    new_data['author'] = papis.document.author_list_to_author(new_data)
    return new_data


def _get_crossref_works(
        **kwargs: Any) -> habanero.request_class.Request:
    cr = habanero.Crossref()
    return cr.works(**kwargs)


def get_data(
        query: str = "",
        author: str = "",
        title: str = "",
        dois: List[str] = [],
        max_results: int = 0,
        filters: Dict[str, Any] = {},
        sort: str = "score",
        order: str = "desc") -> List[Dict[str, Any]]:
    global _filter_names
    global _sort_values
    assert(sort in _sort_values), 'Sort value not valid'
    assert(order in _order_values), 'Sort value not valid'
    if filters:
        if not set(filters.keys()) & _filter_names == set(filters.keys()):
            raise Exception(
                'Filter keys must be one of {0}'
                .format(','.join(_filter_names))
            )
    data = dict(
        query=query, query_author=author,
        ids=dois,
        query_title=title, limit=max_results
    )
    kwargs = {key: data[key] for key in data if data[key]}
    if not dois:
        kwargs.update(dict(sort=sort, order=order))
    try:
        results = _get_crossref_works(filter=filters, **kwargs)
    except Exception as e:
        LOGGER.error(e)
        return []

    if isinstance(results, list):
        docs = [d["message"] for d in results]
    elif isinstance(results, dict):
        if 'message' not in results.keys():
            LOGGER.error("Error retrieving from xref: incorrect message")
            return []
        message = results['message']
        if "items" in message.keys():
            docs = message['items']
        else:
            docs = [message]
    else:
        LOGGER.error("Error retrieving from xref: incorrect message")
        return []
    LOGGER.debug("Retrieved %s documents", len(docs))
    return [
        crossref_data_to_papis_data(d)
        for d in docs]


def doi_to_data(doi_string: str) -> Dict[str, Any]:
    """Search through crossref and get a dictionary containing the data

    :param doi_string: Doi identificator or an url with some doi
    :type  doi_string: str
    :returns: Dictionary containing the data
    :raises ValueError: If no data could be retrieved for the doi

    """
    global LOGGER
    doi_string = doi.get_clean_doi(doi_string)
    results = get_data(dois=[doi_string])
    if results:
        return results[0]
    raise ValueError("Couldn't get data for doi ({})".format(doi_string))


@click.command('crossref')
@click.pass_context
@click.help_option('--help', '-h')
@click.option('--query', '-q', help='General query', default="")
@click.option('--author', '-a', help='Author of the query', default="")
@click.option('--title', '-t', help='Title of the query', default="")
@click.option(
    '--max', '-m', '_ma', help='Maximum number of results', default=20)
@click.option(
    '--filter', '-f', '_filters', help='Filters to apply', default=(),
    type=(click.Choice(_filter_names), str),
    multiple=True)
@click.option(
    '--order', '-o', help='Order of appearance according to sorting',
    default='desc', type=click.Choice(_order_values), show_default=True)
@click.option(
    '--sort', '-s', help='Sorting parameter', default='score',
    type=click.Choice(_sort_values), show_default=True)
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
    Look for documents on crossref.org.

    Examples of its usage are

    papis explore crossref -a 'Albert einstein' pick export --bibtex lib.bib

    """
    logger = logging.getLogger('explore:crossref')
    logger.info('Looking up...')
    data = get_data(
        query=query,
        author=author,
        title=title,
        max_results=_ma,
        filters=dict(_filters),
        sort=sort,
        order=order)
    docs = [papis.document.from_data(data=d) for d in data]
    ctx.obj['documents'] += docs
    logger.info('%s documents found', len(docs))


class DoiFromPdfImporter(papis.importer.Importer):

    """Importer parsing a doi from a pdf file"""

    def __init__(self, uri: str) -> None:
        """The uri should be a filepath"""
        papis.importer.Importer.__init__(self, name='pdf2doi', uri=uri)
        self.doi = None  # type: Optional[str]

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        """The uri should be a filepath"""
        filepath = uri
        if (os.path.isdir(filepath) or not os.path.exists(filepath) or
                not papis.filetype.get_document_extension(filepath) == 'pdf'):
            return None
        importer = DoiFromPdfImporter(filepath)
        importer.fetch()
        return importer if importer.doi else None

    def fetch(self) -> None:
        self.logger.info("Trying to parse doi from file {0}".format(self.uri))
        if self.ctx:
            return
        if not self.doi:
            self.doi = doi.pdf_to_doi(self.uri, maxlines=2000)
        if self.doi:
            self.logger.info("Parsed doi {0}".format(self.doi))
            self.logger.warning(
                "There is no guarantee that this doi is the one")
            importer = Importer(uri=self.doi)
            importer.fetch()
            self.ctx = importer.ctx


class Importer(papis.importer.Importer):

    """Importer getting files and data form a doi through crossref.org"""

    def __init__(self, uri: str) -> None:
        papis.importer.Importer.__init__(self, name='doi', uri=uri)

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
        if 'doi' in data:
            return Importer(uri=data['doi'])
        return None

    def fetch(self) -> None:
        self.logger.info("Using DOI '%s'", self.uri)
        doidata = papis.crossref.get_data(dois=[self.uri])
        if doidata:
            self.ctx.data = doidata[0]
            doc_url = self.ctx.data.get(
                    papis.config.getstring("doc-url-key-name"),
                    None)

            if doc_url is not None:
                self.logger.info(
                    "Trying to download document from %s..", doc_url)
                session = requests.Session()
                session.headers = requests.structures.CaseInsensitiveDict({
                    "user-agent": papis.config.getstring("user-agent")})

                import filetype
                response = session.get(doc_url, allow_redirects=True)
                kind = filetype.guess(response.content)

                if response.status_code != requests.codes.ok:
                    self.logger.info("Could not download document. "
                                     "HTTP status: %s (%d)",
                                     response.reason, response.status_code)
                elif kind is None:
                    self.logger.info("Downloaded document does not have a "
                                     "recognizable (binary) mimetype: '%s'",
                                     response.headers["Content-Type"])
                else:
                    with tempfile.NamedTemporaryFile(
                            mode="wb+",
                            suffix=".{}".format(kind.extension),
                            delete=False) as f:
                        f.write(response.content)
                        self.logger.debug("Saving in %s", f.name)
                        self.ctx.files.append(f.name)


class FromCrossrefImporter(papis.importer.Importer):

    """Importer that gets data from querying to crossref"""

    def __init__(self, uri: str) -> None:
        papis.importer.Importer.__init__(self, uri=uri, name='crossref')

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        # There is no way to check if it matches
        return None

    @classmethod
    def match_data(
            cls, data: Dict[str, Any]) -> Optional[papis.importer.Importer]:
        if 'title' in data:
            return FromCrossrefImporter(uri=data['title'])
        return None

    def fetch_data(self) -> None:
        self.logger.info("querying '{0}' to crossref.org".format(self.uri))
        docs = [
            papis.document.from_data(d)
            for d in get_data(query=self.uri)]
        if docs:
            self.logger.info("got {0} matches, picking...".format(len(docs)))
            docs = list(papis.pick.pick_doc(docs))
            if not docs:
                return
            doc = docs[0]
            importer = Importer(uri=doc['doi'])
            importer.fetch()
            self.ctx = importer.ctx


class Downloader(papis.downloaders.Downloader):

    def __init__(self, uri: str):
        papis.downloaders.Downloader.__init__(self, uri=uri, name="doi")

    @classmethod
    def match(cls, uri: str) -> Optional[papis.downloaders.Downloader]:
        if doi.find_doi_in_text(uri):
            return Downloader(uri)
        else:
            return None

    def fetch(self) -> None:
        _doi = doi.find_doi_in_text(self.uri)
        if _doi is None:
            return None
        importer = Importer(uri=_doi)
        importer.fetch()
        self.ctx = importer.ctx
