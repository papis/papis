import re
from typing import (
    Any, List, Dict, Iterator, Tuple, Union, Pattern,
    TypedDict, TYPE_CHECKING)

import papis.config
import papis.document
import papis.importer
import papis.utils

if TYPE_CHECKING:
    import bs4


class MetaEquivalence(TypedDict):
    tag: str
    key: str
    attrs: Dict[str, Union[str, Pattern[str]]]


meta_equivalences: List[MetaEquivalence] = [
    # google
    {"tag": "meta", "key": "abstract", "attrs": {"name": "description"}},
    {"tag": "meta", "key": "doi", "attrs": {"name": "doi"}},
    {"tag": "meta", "key": "keywords", "attrs": {"name": "keywords"}},
    {"tag": "title", "key": "title", "attrs": {}},
    # facebook
    {"tag": "meta", "key": "type", "attrs": {"property": "og:type"}},
    {"tag": "meta",
        "key": "abstract", "attrs": {"property": "og:description"}},
    {"tag": "meta", "key": "title", "attrs": {"property": "og:title"}},
    {"tag": "meta", "key": "url", "attrs": {"property": "og:url"}},
    # citation style
    # https://scholar.google.com/intl/en/scholar/inclusion.html#indexing
    {"tag": "meta", "key": "doi", "attrs": {"name": "citation_doi"}},
    {"tag": "meta",
        "key": "firstpage", "attrs": {"name": "citation_firstpage"}},
    {"tag": "meta", "key": "lastpage", "attrs": {"name": "citation_lastpage"}},
    {"tag": "meta",
        "key": "url", "attrs": {"name": "citation_fulltext_html_url"}},
    {"tag": "meta", "key": "pdf_url", "attrs": {"name": "citation_pdf_url"}},
    {"tag": "meta", "key": "issn", "attrs": {"name": "citation_issn"}},
    {"tag": "meta", "key": "issue", "attrs": {"name": "citation_issue"}},
    {"tag": "meta", "key": "abstract", "attrs": {"name": "citation_abstract"}},
    {"tag": "meta",
        "key": "journal_abbrev", "attrs": {"name": "citation_journal_abbrev"}},
    {"tag": "meta",
        "key": "journal", "attrs": {"name": "citation_journal_title"}},
    {"tag": "meta", "key": "language", "attrs": {"name": "citation_language"}},
    {"tag": "meta",
        "key": "online_date", "attrs": {"name": "citation_online_date"}},
    {"tag": "meta",
        "key": "publication_date",
        "attrs": {"name": "citation_publication_date"}},
    {"tag": "meta",
        "key": "publisher", "attrs": {"name": "citation_publisher"}},
    {"tag": "meta", "key": "title", "attrs": {"name": "citation_title"}},
    {"tag": "meta", "key": "volume", "attrs": {"name": "citation_volume"}},
    # dc.{id} style
    {"tag": "meta",
        "key": "publisher",
        "attrs": {"name": re.compile(r"dc.publisher", re.I)}},
    {"tag": "meta",
        "key": "publisher",
        "attrs": {"name": re.compile(r".*st.publisher.*", re.I)}},
    {"tag": "meta",
        "key": "date", "attrs": {"name": re.compile(r"dc.date", re.I)}},
    {"tag": "meta",
        "key": "language", "attrs": {"name": re.compile(r"dc.language", re.I)}},
    {"tag": "meta",
        "key": "issue",
        "attrs": {"name": re.compile(r"dc.citation.issue", re.I)}},
    {"tag": "meta",
            "key": "volume",
            "attrs": {"name": re.compile(r"dc.citation.volume", re.I)}},
    {"tag": "meta",
            "key": "keywords",
            "attrs": {"name": re.compile(r"dc.subject", re.I)}},
    {"tag": "meta",
            "key": "title", "attrs": {"name": re.compile(r"dc.title", re.I)}},
    {"tag": "meta",
            "key": "type", "attrs": {"name": re.compile(r"dc.type", re.I)}},
    {"tag": "meta",
            "key": "abstract",
            "attrs": {"name": re.compile(r"dc.description", re.I)}},
    {"tag": "meta",
            "key": "abstract",
            "attrs": {"name": re.compile(r"dc.description.abstract", re.I)}},
    {"tag": "meta",
            "key": "journal_abbrev",
            "attrs": {"name": re.compile(r"dc.relation.ispartof", re.I)}},
    {"tag": "meta",
            "key": "year", "attrs": {"name": re.compile(r"dc.issued", re.I)}},
    {"tag": "meta",
            "key": "doi",
            "attrs": {"name": re.compile(r"dc.identifier", re.I),
                      "scheme": "doi"}},
]


def parse_meta_headers(soup: "bs4.BeautifulSoup") -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for equiv in meta_equivalences:
        elements = soup.find_all(equiv["tag"], attrs=equiv["attrs"])
        if elements:
            value = elements[0].attrs.get("content")
            data[equiv["key"]] = str(value).replace("\r", "")

    author_list = parse_meta_authors(soup)
    if author_list:
        data["author_list"] = author_list
        data["author"] = papis.document.author_list_to_author(data)

    from papis.bibtex import bibtex_type_converter

    bib_type = data.get("type")
    if bib_type in bibtex_type_converter:
        data["type"] = bibtex_type_converter[bib_type]

    return data


def parse_meta_authors(soup: "bs4.BeautifulSoup") -> List[Dict[str, Any]]:
    # find author tags
    authors = soup.find_all(name="meta", attrs={"name": "citation_author"})
    if not authors:
        authors = soup.find_all(
            name="meta", attrs={"name": re.compile(r"dc.creator", re.I)})

    if not authors:
        return []

    # find affiliation tags
    affs = soup.find_all(
        name="meta",
        attrs={"name": "citation_author_institution"})

    if affs and len(authors) == len(affs):
        authors_and_affs: Iterator[Tuple[Any, Any]] = zip(authors, affs)
    else:
        authors_and_affs = ((a, None) for a in authors)

    # convert to papis author format
    author_list: List[Dict[str, Any]] = []
    for author, aff in authors_and_affs:
        fullname = papis.document.split_author_name(author.get("content"))
        affiliation = [{"name": aff.get("content")}] if aff else []

        author_list.append({
            "given": fullname["given"],
            "family": fullname["family"],
            "affiliation": affiliation,
            })

    return author_list
