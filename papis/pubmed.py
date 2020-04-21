from typing import Any, Dict, List, Optional

import json
import urllib
import requests

import papis.importer
import papis.document
import papis.downloaders.base

# https://api.ncbi.nlm.nih.gov/lit/ctxp
PUBMED_DATABASE = "pubmed"
PUBMED_URL = \
    "https://api.ncbi.nlm.nih.gov/lit/ctxp/v1/{database}/?format=csl&id={pmid}"


# https://docs.citationstyles.org/en/1.0.1/specification.html#appendix-iii-types
type_converter = {
    "article": "article",
    "article-journal": "article",
    "book": "book",
    "chapter": "inbook",
    "paper-conference": "inproceedings",
    "report": "report",
    "thesis": "phdthesis",
}   # type: Dict[str, str]


KeyConversionPair = papis.document.KeyConversionPair
key_conversion = [
    KeyConversionPair("container-title", [{"key": "journal", "action": None}]),
    KeyConversionPair("PMID", [
        {"key": "pmid", "action": None},
        {"key": "ref", "action": lambda x: "pmid{}".format(x)}
        ]),
    KeyConversionPair("ISSN", [{"key": "issn", "action": None}]),
    KeyConversionPair("DOI", [{"key": "doi", "action": None}]),
    KeyConversionPair("page", [
        {"key": "pages", "action": lambda x: handle_pubmed_pages(x)}
        ]),
    KeyConversionPair("type", [
        {"key": "type", "action": lambda x: type_converter.get(x, "misc")}
        ]),
    KeyConversionPair("author", [{"key": "author_list", "action": None}]),
    KeyConversionPair("issued", [
        {"key": "year", "action": lambda x: x["date-parts"][0][0]},
        ]),
    KeyConversionPair("volume", [papis.document.EmptyKeyConversion]),
    KeyConversionPair("issue", [papis.document.EmptyKeyConversion]),
    KeyConversionPair("title", [papis.document.EmptyKeyConversion]),
    KeyConversionPair("publisher", [papis.document.EmptyKeyConversion]),
]   # type: List[KeyConversionPair]


def handle_pubmed_pages(pages: str) -> str:
    # returned data is in the form 561-7 meaning 562-567
    start, end = [x.strip() for x in pages.split("-")]
    end = "{}{}".format(start[:max(0, len(start) - len(end))], end)

    return "{}--{}".format(start, end)


def pubmed_data_to_papis_data(data: Dict[str, Any]) -> Dict[str, Any]:
    new_data = papis.document.keyconversion_to_data(key_conversion, data)
    new_data["author"] = papis.document.author_list_to_author(new_data)

    return new_data


def is_valid_pmid(pmid: str) -> bool:
    pmid = pmid.strip()
    if not pmid.isdigit():
        return False

    url = PUBMED_URL.format(pmid=pmid, database=PUBMED_DATABASE)
    request = urllib.request.Request(url)

    from urllib.error import HTTPError, URLError
    try:
        urllib.request.urlopen(request)
    except (HTTPError, URLError):
        return False

    return True


def get_data(query: str = "") -> Dict[str, Any]:
    # NOTE: being nice and using the project version as a user agent
    # as requested in https://api.ncbi.nlm.nih.gov/lit/ctxp
    import papis
    headers = requests.structures.CaseInsensitiveDict({
        'user-agent': "papis/{}".format(papis.__version__)
        })

    session = requests.Session()
    session.headers = headers
    response = session.get(PUBMED_URL.format(
        pmid=query.strip(), database=PUBMED_DATABASE))

    return pubmed_data_to_papis_data(json.loads(response.content))


class Importer(papis.importer.Importer):
    """Importer downloading data from a pubmed id"""

    def __init__(self, uri: str = ''):
        papis.importer.Importer.__init__(self, name='pubmed', uri=uri)

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        if is_valid_pmid(uri):
            return Importer(uri)

        return None

    def fetch(self) -> None:
        self.ctx.data = get_data(self.uri)
