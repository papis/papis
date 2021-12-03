import re
from typing import Dict, Optional, Any, List

import papis.downloaders
import papis.document

_K = papis.document.KeyConversionPair


def _page_to_pages(data: List[Dict[str, str]]) -> str:
    if len(data) == 0:
        raise RuntimeError("No data to turn to pages")
    x = data[0]
    if not {"first-page", "last-page"} & x.keys():
        raise RuntimeError("first-page and last-page not found")
    return "{0}--{1}".format(x["first-page"], x["last-page"])


article_keyconv = [
    _K("doi", [papis.document.EmptyKeyConversion]),
    _K("pii", [papis.document.EmptyKeyConversion]),
    _K("language", [papis.document.EmptyKeyConversion]),
    _K("subtitle", [papis.document.EmptyKeyConversion]),
    _K("issn", [papis.document.EmptyKeyConversion]),
    _K("srctitle", [{"key": "journal", "action": None}]),
    _K("vol-first", [{"key": "volume", "action": None}]),
    _K("cover-date-years", [{"key": "year", "action": lambda x: x[0]}]),
    _K("cover-date-start", [{"key": "date", "action": None}]),
    _K("document-type", [{"key": "type", "action": None}]),
    _K("titleString", [{"key": "title", "action": None}]),
    _K("dates", [
        {"key": "accepted-date", "action": lambda x: x["Accepted"]},
        {"key": "publication-date", "action": lambda x: x["Publication date"]}
    ]),
    _K("pages", [{
        "action": _page_to_pages,
        "key": None
    }]),
]  # List[papis.document.KeyConversionPair]
script_keyconv = [
    _K("article", [{
        "key": "_article_data",
        "action": lambda x:
            papis.document.keyconversion_to_data(article_keyconv, x)
    }]),
]  # List[papis.document.KeyConversionPair]


class Downloader(papis.downloaders.Downloader):

    def __init__(self, url: str):
        papis.downloaders.Downloader.__init__(
            self, url, name="sciencedirect")
        self.expected_document_extension = 'pdf'

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        if re.match(r".*\.sciencedirect\.com.*", url):
            return Downloader(url)
        else:
            return None

    def get_data(self) -> Dict[str, Any]:
        global script_keyconv
        data = dict()  # type: Dict[str, Any]
        soup = self._get_soup()
        scripts = soup.find_all(name="script", attrs={'data-iso-key': '_0'})
        if scripts:
            import json
            rawdata = json.loads(scripts[0].text)
            self.logger.debug("Found %d scripts data-iso-key", len(scripts))

            converted_data = papis.document.keyconversion_to_data(
                script_keyconv, rawdata)
            data.update(converted_data["_article_data"])
            # TODO: parse abstract and author in a typed checked and meaningful
            #       way
            # data.update(converted_data["_abstract_data"])
            # data.update(converted_data["_author_data"])
            data['author'] = papis.document.author_list_to_author(data)
        return data
