import re
from typing import Any, List, Dict, Iterator, Tuple, Union, Pattern
from typing_extensions import TypedDict

import bs4

import papis.bibtex
import papis.config
import papis.document
import papis.importer
import papis.utils


MetaEquivalence = TypedDict(
    "MetaEquivalence", {
        "tag": str,
        "key": str,
        "attrs": Dict[str, Union[str, Pattern[str]]],
    }
)

meta_equivalences = [
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
        "attrs": {"name": re.compile("dc.publisher", re.I)}},
    {"tag": "meta",
        "key": "publisher",
        "attrs": {"name": re.compile(".*st.publisher.*", re.I)}},
    {"tag": "meta",
        "key": "date", "attrs": {"name": re.compile("dc.date", re.I)}},
    {"tag": "meta",
        "key": "language", "attrs": {"name": re.compile("dc.language", re.I)}},
    {"tag": "meta",
        "key": "issue",
        "attrs": {"name": re.compile("dc.citation.issue", re.I)}},
    {"tag": "meta",
            "key": "volume",
            "attrs": {"name": re.compile("dc.citation.volume", re.I)}},
    {"tag": "meta",
            "key": "keywords",
            "attrs": {"name": re.compile("dc.subject", re.I)}},
    {"tag": "meta",
            "key": "title", "attrs": {"name": re.compile("dc.title", re.I)}},
    {"tag": "meta",
            "key": "type", "attrs": {"name": re.compile("dc.type", re.I)}},
    {"tag": "meta",
            "key": "abstract",
            "attrs": {"name": re.compile("dc.description", re.I)}},
    {"tag": "meta",
            "key": "abstract",
            "attrs": {"name": re.compile("dc.description.abstract", re.I)}},
    {"tag": "meta",
            "key": "journal_abbrev",
            "attrs": {"name": re.compile("dc.relation.ispartof", re.I)}},
    {"tag": "meta",
            "key": "year", "attrs": {"name": re.compile("dc.issued", re.I)}},
    {"tag": "meta",
            "key": "doi",
            "attrs": {"name": re.compile("dc.identifier", re.I),
                      "scheme": "doi"}},
]  # type: List[MetaEquivalence]


def parse_meta_headers(soup: bs4.BeautifulSoup) -> Dict[str, Any]:
    global meta_equivalences
    # metas = soup.find_all(name="meta")
    data = dict()  # type: Dict[str, Any]
    for equiv in meta_equivalences:
        elements = soup.find_all(equiv['tag'], attrs=equiv["attrs"])
        if elements:
            value = elements[0].attrs.get("content")
            data[equiv["key"]] = str(value).replace('\r', '')

    author_list = parse_meta_authors(soup)
    if author_list:
        data['author_list'] = author_list
        data['author'] = papis.document.author_list_to_author(data)

    return data


def parse_meta_authors(soup: bs4.BeautifulSoup) -> List[Dict[str, Any]]:
    author_list = []  # type: List[Dict[str, Any]]
    authors = soup.find_all(name='meta', attrs={'name': 'citation_author'})
    if not authors:
        authors = soup.find_all(
            name='meta', attrs={'name': re.compile('dc.creator', re.I)})
    affs = soup.find_all(
        name='meta',
        attrs={'name': 'citation_author_institution'})

    if affs and authors:
        tuples = zip(authors, affs)  # type: Iterator[Tuple[Any, Any]]
    elif authors:
        tuples = ((a, None) for a in authors)
    else:
        return []

    for t in tuples:
        fullname = t[0].get('content')
        affiliation = [dict(name=t[1].get('content'))] if t[1] else []
        fullnames = re.split(r'\s+', fullname)
        author_list.append(dict(
            given=fullnames[0],
            family=' '.join(fullnames[1:]),
            affiliation=affiliation,
        ))
    return author_list
