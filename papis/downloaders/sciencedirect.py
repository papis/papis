import re
import bs4
import papis.downloaders.base
import papis.document
import json
import collections
import functools
import logging


def get_author_list(data):
    rdata = []
    assert(isinstance(data, list))
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
    return rdata


script_keyconv = collections.OrderedDict({
    "article": {
        "key": "_article_data",
        "action": lambda x:
            papis.document.keyconversion_to_data(article_keyconv, x)
    },
    "abstracts": {
        "key": "_abstract_data",
        "action": lambda x:
            papis.document.keyconversion_to_data(abstracts_keyconv, x)
    },
    "authors": {
        "key": "_author_data",
        "action": lambda x:
            papis.document.keyconversion_to_data(authors_keyconv, x)
    },
})
authors_keyconv = collections.OrderedDict({
    "content": {
        "key": "aauthor_list",
        "action": lambda x:
        get_author_list(
            list(
                functools.reduce(lambda s, t: s+t,
                    map(lambda s: s["$$"],
                    filter(lambda s: s["#name"] == "author-group",
                        x)))))
    }
})
abstracts_keyconv = collections.OrderedDict({
    "content": {
        "key": "abstract",
        "action": lambda x: " ".join(
        map(lambda s: s["_"],
            functools.reduce(lambda s, t: s + t,
                map(lambda s: s["$$"],
                    filter(lambda s: s["#name"] == 'abstract-sec',
                        functools.reduce(lambda s, t: s+t,
                            map(lambda s: s["$$"],
                                filter(lambda s: s['$']['class'] == 'author',
                                    x)))))))
        )
    }
})
article_keyconv = collections.OrderedDict({
    "doi": {},
    "pii": {},
    "language": {},
    "subtitle": {},
    "issn": {},
    "srctitle": {"key": "journal"},
    "vol-first": {"key": "volume"},
    "cover-date-years": {"key": "year", "action": lambda x: x[0]},
    "cover-date-start": {"key": "date"},
    "document-type": {"key": "type"},
    "titleString": {"key": "title"},
    "dates": [
        {"key": "accepted-date", "action": lambda x: x["Accepted"]},
        {"key": "publication-date", "action": lambda x: x["Publication date"]}
    ],
    "pages": {
        "action": lambda x: "{x[first-page]}--{x[last-page]}".format(x=x[0])
    },
})


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(
            self, url, name="sciencedirect"
        )
        self.expected_document_extension = 'pdf'

    @classmethod
    def match(cls, url):
        if re.match(r".*\.sciencedirect\.com.*", url):
            return Downloader(url)
        else:
            return False

    def _get_body(self):
        return self.session.get(self.uri).content.decode('utf-8')

    def get_data(self):
        data = dict()
        body = self._get_body()
        soup = bs4.BeautifulSoup(body, "html.parser")
        scripts = soup.find_all(name="script", attrs={'data-iso-key': '_0'})
        if scripts:
            rdata = json.loads(scripts[0].text)
            self.logger.debug(
                "found {0} scripts data-iso-key".format(len(scripts)))
            converted_data = papis.document.keyconversion_to_data(
                script_keyconv, rdata)
            data.update(converted_data["_article_data"])
            data.update(converted_data["_abstract_data"])
            data.update(converted_data["_author_data"])
        return data
