import os
import logging
import requests
import papis.config
import papis.document
import papis.utils
import filetype
import papis.importer
import papis.bibtex
import tempfile
import copy
import re
import bs4

from typing import (
    NamedTuple, Any,
    List, Dict, Union, Pattern, Callable, Optional
    )
from typing_extensions import TypedDict

MetaEquivalence = TypedDict(
    "MetaEquivalence",
    {
    "tag": str,
    "key": str,
    "attrs": Dict[str, Union[str, Pattern[str]]],
    }
);

meta_equivalences = [
# google
{"tag": "meta", "key": "abstract", "attrs": {"name": "description"}},
{"tag": "meta", "key": "doi", "attrs": {"name": "doi"}},
{"tag": "meta", "key": "keywords", "attrs": {"name": "keywords"}},
#{"tag": "title", "key": "title", "attrs": {}, "action": lambda e: e.text},
{"tag": "title", "key": "title", "attrs": {}},
# facebook
{"tag": "meta", "key": "type", "attrs": {"property": "og:type"}},
{"tag": "meta", "key": "abstract", "attrs": {"property": "og:description"}},
{"tag": "meta", "key": "title", "attrs": {"property": "og:title"}},
{"tag": "meta", "key": "url", "attrs": {"property": "og:url"}},
# citation style
# https://scholar.google.com/intl/en/scholar/inclusion.html#indexing
{"tag": "meta", "key": "doi", "attrs": {"name": "citation_doi"}},
{"tag": "meta", "key": "firstpage", "attrs": {"name": "citation_firstpage"}},
{"tag": "meta", "key": "lastpage", "attrs": {"name": "citation_lastpage"}},
{"tag": "meta", "key": "url", "attrs": {"name": "citation_fulltext_html_url"}},
{"tag": "meta", "key": "pdf_url", "attrs": {"name": "citation_pdf_url"}},
{"tag": "meta", "key": "issn", "attrs": {"name": "citation_issn"}},
{"tag": "meta", "key": "issue", "attrs": {"name": "citation_issue"}},
{"tag": "meta", "key": "abstract", "attrs": {"name": "citation_abstract"}},
{"tag": "meta", "key": "journal_abbrev", "attrs": {"name": "citation_journal_abbrev"}},
{"tag": "meta", "key": "journal", "attrs": {"name": "citation_journal_title"}},
{"tag": "meta", "key": "language", "attrs": {"name": "citation_language"}},
{"tag": "meta", "key": "online_date", "attrs": {"name": "citation_online_date"}},
{"tag": "meta", "key": "publication_date", "attrs": {"name": "citation_publication_date"}},
{"tag": "meta", "key": "publisher", "attrs": {"name": "citation_publisher"}},
{"tag": "meta", "key": "title", "attrs": {"name": "citation_title"}},
{"tag": "meta", "key": "volume", "attrs": {"name": "citation_volume"}},
# dc.{id} style
{"tag": "meta", "key": "publisher", "attrs": {"name": re.compile("dc.publisher", re.I)}},
{"tag": "meta", "key": "publisher", "attrs": {"name": re.compile(".*st.publisher.*", re.I)}},
{"tag": "meta", "key": "date", "attrs": {"name": re.compile("dc.date", re.I)}},
{"tag": "meta", "key": "language", "attrs": {"name": re.compile("dc.language", re.I)}},
{"tag": "meta", "key": "issue", "attrs": {"name": re.compile("dc.citation.issue", re.I)}},
{"tag": "meta", "key": "volume", "attrs": {"name": re.compile("dc.citation.volume", re.I)}},
{"tag": "meta", "key": "keywords", "attrs": {"name": re.compile("dc.subject", re.I)}},
{"tag": "meta", "key": "title", "attrs": {"name": re.compile("dc.title", re.I)}},
{"tag": "meta", "key": "type", "attrs": {"name": re.compile("dc.type", re.I)}},
{"tag": "meta", "key": "abstract", "attrs": {"name": re.compile("dc.description", re.I)}},
{"tag": "meta", "key": "abstract", "attrs": {"name": re.compile("dc.description.abstract", re.I)}},
{"tag": "meta", "key": "journal_abbrev", "attrs": {"name": re.compile("dc.relation.ispartof", re.I)}},
{"tag": "meta", "key": "year", "attrs": {"name": re.compile("dc.issued", re.I)}},
{"tag": "meta", "key": "doi", "attrs": {"name": re.compile("dc.identifier", re.I), "scheme": "doi"}},
]  # type: List[MetaEquivalence]


def parse_meta_headers(soup: bs4.BeautifulSoup) -> Dict[str, Any]:
    global meta_equivalences
    #metas = soup.find_all(name="meta")
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
    affs = soup.find_all(name='meta',
            attrs={'name': 'citation_author_institution'})
    if affs and authors:
        tuples = zip(authors, affs)
    elif authors:
        tuples = [(a, None) for a in authors]
    else:
        return []

    for t in tuples:
        fullname = t[0].get('content')
        affiliation = [dict(name=t[1].get('content'))] if t[1] else []
        fullnames = re.split('\s+', fullname)
        author_list.append(dict(
            given=fullnames[0],
            family=' '.join(fullnames[1:]),
            affiliation=affiliation,
        ))
    return author_list


class Downloader(papis.importer.Importer):

    """This is the base class for every downloader.
    """

    def __init__(
            self,
            uri: str = "",
            name: str = "",
            ctx: papis.importer.Context = papis.importer.Context()):
        self.ctx = ctx
        self.uri = uri
        self.name = name or os.path.basename(__file__)
        self.logger = logging.getLogger("downloader:"+self.name)
        self.logger.debug("uri {0}".format(uri))
        self.expected_document_extension = None  # type: Optional[str]
        self.priority = 1  # type: int
        self._soup = None  # type: Optional[bs4.BeautifulSoup]

        self.bibtex_data = None  # type: Optional[str]
        self.document_data = None  # type: Optional[bytes]

        self.session = requests.Session()  # type: requests.Session
        self.session.headers = requests.structures.CaseInsensitiveDict({
            'User-Agent': papis.config.getstring('user-agent')
        })
        proxy = papis.config.get('downloader-proxy')
        if proxy is not None:
            self.session.proxies = {
                'http': proxy,
                'https': proxy,
            }
        self.cookies = {}  # type: Dict[str, str]

    def fetch_data(self) -> None:
        """
        Try first to get data by hand with the get_data command.
        Then commplement with bibtex data.
        """
        # Try with get_data
        try:
            data = self.get_data()
            assert(isinstance(data, dict))
        except NotImplementedError:
            pass
        else:
            self.ctx.data.update(data)

        # try with bibtex
        try:
            self.download_bibtex()
        except NotImplementedError:
            pass
        else:
            bib_rawdata = self.get_bibtex_data()
            if bib_rawdata:
                datalist = papis.bibtex.bibtex_to_dict(bib_rawdata)
                if datalist:
                    self.logger.info("Merging data from bibtex")
                    self.ctx.data.update(datalist[0])
        # try getting doi
        try:
            doi = self.get_doi()
        except NotImplementedError:
            pass
        else:
            self.ctx.data['doi'] = doi


    def fetch_files(self) -> None:
        # get documents
        try:
            self.download_document()
        except NotImplementedError:
            pass
        else:
            doc_rawdata = self.get_document_data()
            if doc_rawdata and self.check_document_format():
                tmp = tempfile.mktemp()
                self.logger.info("Saving downloaded file in {0}".format(tmp))
                with open(tmp, 'wb+') as fd:
                    fd.write(doc_rawdata)
                self.ctx.files.append(tmp)

    def fetch(self) -> None:
        self.fetch_data()
        self.fetch_files()

    def _get_body(self) -> bytes:
        """Get body of the uri, this is also important for unittesting"""
        return self.session.get(self.uri).content

    def _get_soup(self) -> bs4.BeautifulSoup:
        """Get body of the uri, this is also important for unittesting"""
        if self._soup:
            return self._soup
        self._soup = bs4.BeautifulSoup(self._get_body(), features='lxml')
        return self._soup

    def __str__(self) -> str:
        return 'Downloader({0}, uri={1})'.format(self.name, self.uri)

    def get_bibtex_url(self) -> Optional[str]:
        """It returns the urls that is to be access to download
        the bibtex information. It has to be implemented for every
        downloader, or otherwise it will raise an exception.

        :returns: Bibtex url
        :rtype:  str
        """
        raise NotImplementedError(
            "Getting bibtex url not implemented for this downloader")

    def get_bibtex_data(self) -> Optional[str]:
        """Get the bibtex_data data if it has been downloaded already
        and if not download it and return the data in utf-8 format.

        :returns: Bibtex data in utf-8 format
        :rtype:  str
        """
        if not self.bibtex_data:
            self.download_bibtex()
        return self.bibtex_data

    def download_bibtex(self) -> None:
        """Bibtex downloader, it should try to download bibtex information from
        the url provided by ``get_bibtex_url``.

        It sets the ``bibtex_data`` attribute if it succeeds.

        :returns: Nothing
        :rtype:  None
        """
        url = self.get_bibtex_url()
        if not url:
            return
        res = self.session.get(url, cookies=self.cookies)
        self.logger.info("downloading bibtex from {0}".format(url))
        self.bibtex_data = res.content.decode()

    def get_document_url(self) -> Optional[str]:
        """It returns the urls that is to be access to download
        the document information. It has to be implemented for every
        downloader, or otherwise it will raise an exception.

        :returns: Document url
        :rtype:  str
        """
        raise NotImplementedError(
            "Getting bibtex url not implemented for this downloader")

    def get_data(self) -> Dict[str, Any]:
        """A general data retriever, for instance when data needn't need
        to come from a bibtex
        """
        raise NotImplementedError(
            "Getting general data is not implemented for this downloader")

    def get_doi(self) -> Optional[str]:
        """It returns the doi of the document, if it is retrievable.
        It has to be implemented for every downloader, or otherwise it will
        raise an exception.

        :returns: Document doi
        :rtype:  str
        """
        raise NotImplementedError(
            "Getting document url not implemented for this downloader")

    def get_document_data(self) -> Optional[bytes]:
        """Get the document_data data if it has been downloaded already
        and if not download it and return the data in binary format.

        :returns: Document data in binary format
        :rtype:  str
        """
        if not self.document_data:
            self.download_document()
        return self.document_data

    def download_document(self) -> None:
        """Document downloader, it should try to download document information from
        the url provided by ``get_document_url``.

        It sets the ``document_data`` attribute if it succeeds.

        :returns: Nothing
        :rtype:  None
        """
        url = self.get_document_url()
        if not url:
            return
        self.logger.info("downloading file from {0}".format(url))
        res = self.session.get(url, cookies=self.cookies)
        self.document_data = res.content

    def check_document_format(self) -> bool:
        """Check if the downloaded document has the filetype that the
        downloader expects. If the downloader does not expect any special
        filetype, accept anything because there is no way to know if it is
        correct.

        :returns: True if it is of the right type, else otherwise
        :rtype:  bool
        """
        def print_warning() -> None:
            self.logger.error(
                "The downloaded data does not seem to be of"
                "the correct type ({})"
                .format(self.expected_document_extension))

        if self.expected_document_extension is None:
            return True

        retrieved_kind = filetype.guess(self.get_document_data())

        if retrieved_kind is None:
            print_warning()
            return False

        self.logger.debug(
            'retrieved kind of document seems to be {0}'
            .format(retrieved_kind.mime))

        if not isinstance(self.expected_document_extension, list):
            expected_document_extensions = [self.expected_document_extension]

        if retrieved_kind.extension in expected_document_extensions:
            return True
        else:
            print_warning()
            return False
