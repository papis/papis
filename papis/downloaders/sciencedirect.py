import re
import papis.downloaders.base
import papis.document
import json
import collections
import functools
from typing import (
    Dict, Optional, Any, List, Union, NamedTuple, Callable, Tuple, Sequence, TypeVar)

_K = papis.document.KeyConversionPair
A = TypeVar("A")
B = TypeVar("B")


def fmap(fun: Callable[[A], B], value: Optional[A]) -> Optional[B]:
    return fun(value) if value is not None else None


def get_author_list(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rdata = []  # type: List[Dict[str, Any]]
    for d in data:
        if d["#name"] == "author":
            author_data = dict()
            for prop in d["$$"]:
                if prop["#name"] == "given-name":
                    author_data["given"] = prop["_"]
                elif prop["#name"] == "surname":
                    author_data["family"] = prop["_"]
                elif prop["#name"] == "cross-ref":
                    author_data["refid"] = prop["$"]["refid"]
            rdata.append(author_data)
        if d["#name"] == "affiliation":
            affid = d["$"]["id"]
            text = functools.reduce(lambda x, y: x + y,
                map(lambda x: x["_"],
                    filter(lambda x: x["#name"] == "textfn",
                        d["$$"])))
            authors = list(filter(lambda a: a.get("refid") == affid, rdata))
            if authors:
                authors[0]["affiliation"] = [dict(name=text)]
                del authors[0]["refid"]
            else:
                if len(rdata) == 1:
                    rdata[0]["affiliation"] = [dict(name=text)]
    return rdata


authors_keyconv = [
    _K("content", [{
        "key": "author_list",
        "action": lambda x:
        get_author_list(
            list(
                functools.reduce(lambda s, t: s+t,
                    map(lambda s: s["$$"],
                    filter(lambda s: s["#name"] == "author-group",
                        x)))))
    }])
]  # List[papis.document.KeyConversionPair]
"""
abstracts_keyconv = [_K(
    "content",
    [
        {  # Single author format
            "key": "abstract",
            "action": lambda x: " ".join(
                map(lambda s: s["_"],
                    functools.reduce(lambda s, t: s + t,
                        map(lambda s: s["$$"],
                            filter(lambda s: s["#name"] == 'abstract-sec',
                                functools.reduce(lambda s, t: s+t,
                                    map(lambda s: s["$$"],
                                        filter(lambda s:
                                            s['$']['class'] == 'author',
                                            x)))))))
            )
        },
        { # multiple author format (apparently)
            "key": "abstract",
            "action": lambda x: " ".join(
                map(lambda s: s['_'],
                    functools.reduce(lambda x, y: x + y,
                        map(lambda s: s["$$"],
                            filter(lambda s: s['#name'] == 'simple-para',
                                functools.reduce(lambda x, y: x + y,
                                    map(lambda s: s["$$"],
                                        filter(lambda s: s["#name"] == 'abstract-sec',
                                            functools.reduce(lambda x, y: x + y,
                                                map(lambda s: s["$$"],
                                                    filter(lambda s: s['$']['class'] == 'author',
                                                        x)))))))))))
        }
    ]
)]  # List[papis.document.KeyConversionPair]
"""
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
        "action": lambda x: "{x[first-page]}--{x[last-page]}".format(x=x[0]),
        "key": None
    }]),
]  # List[papis.document.KeyConversionPair]
script_keyconv = [
    _K("article", [{
        "key": "_article_data",
        "action": lambda x:
            papis.document.keyconversion_to_data(article_keyconv, x)
    }]),
    _K("abstracts", [{
        "key": "_abstract_data",
        "action": lambda x:
            papis.document.keyconversion_to_data(abstracts_keyconv, x)
    }]),
    _K("authors", [{
        "key": "_author_data",
        "action": lambda x:
            papis.document.keyconversion_to_data(authors_keyconv, x)
    }]),
]  # List[papis.document.KeyConversionPair]


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url: str):
        papis.downloaders.base.Downloader.__init__(
            self, url, name="sciencedirect")
        self.expected_document_extension = 'pdf'

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.base.Downloader]:
        if re.match(r".*\.sciencedirect\.com.*", url):
            return Downloader(url)
        else:
            return None

    def get_data(self) -> Dict[str, Any]:
        global script_keyconv
        data = dict()
        soup = self._get_soup()
        scripts = soup.find_all(name="script", attrs={'data-iso-key': '_0'})
        if scripts:
            rawdata = json.loads(scripts[0].text)
            self.logger.debug(
                "found {0} scripts data-iso-key".format(len(scripts)))
            converted_data = papis.document.keyconversion_to_data(
                script_keyconv, rawdata)
            data.update(converted_data["_article_data"])
            data.update(converted_data["_abstract_data"])
            data.update(converted_data["_author_data"])
            data['author'] = papis.document.author_list_to_author(data)
        return data
