import os
import re
import sys
from typing import List, Optional, Any, Sequence, Type, Dict, Union, TYPE_CHECKING

import papis.bibtex
import papis.config
import papis.document
import papis.importer
import papis.plugin
import papis.utils
import papis.logging

if TYPE_CHECKING:
    import bs4

logger = papis.logging.get_logger(__name__)


def _extension_name() -> str:
    return "papis.downloader"


class Importer(papis.importer.Importer):

    """Importer that tries to get data and files from implemented downloaders
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(name="url", **kwargs)

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        return (
            Importer(uri=uri)
            if re.match(" *http(s)?.*", uri) is not None
            else None
        )

    def fetch(self) -> None:
        self.logger.info("Attempting to import from url '%s'", self.uri)
        self.ctx = get_info_from_url(self.uri) or papis.importer.Context()

    def fetch_data(self) -> None:
        pass

    def fetch_files(self) -> None:
        pass


class Downloader(papis.importer.Importer):

    """This is the base class for every downloader.
    """

    def __init__(self,
                 uri: str = "",
                 name: str = "",
                 ctx: Optional[papis.importer.Context] = None,
                 expected_document_extension: Optional[Union[str, List[str]]] = None,
                 cookies: Optional[Dict[str, str]] = None,
                 priority: int = 1,
                 ) -> None:
        if ctx is None:
            ctx = papis.importer.Context()

        if cookies is None:
            cookies = {}

        super().__init__(
            uri=uri,
            ctx=ctx,
            name=name or os.path.basename(__file__))
        self.logger = papis.logging.get_logger("papis.downloader.{}".format(self.name))
        self.logger.debug("uri '%s'", uri)

        self.expected_document_extension = expected_document_extension
        self.priority = priority
        self._soup = None  # type: Optional[bs4.BeautifulSoup]

        self.bibtex_data = None  # type: Optional[str]
        self.document_data = None  # type: Optional[bytes]

        import requests
        self.session = requests.Session()  # type: requests.Session
        self.session.headers = requests.structures.CaseInsensitiveDict({
            "User-Agent": papis.config.getstring("user-agent")
        })
        proxy = papis.config.get("downloader-proxy")
        if proxy is not None:
            self.session.proxies = {
                "http": proxy,
                "https": proxy,
            }
        self.cookies = cookies

    def fetch_data(self) -> None:
        """
        Try first to get data by hand with the get_data command.
        Then commplement with bibtex data.
        """
        # Try with get_data
        try:
            data = self.get_data()
            assert isinstance(data, dict)
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
                    if len(datalist) > 1:
                        self.logger.warning(
                            "'%s' found %d BibTeX entries. Picking first one.",
                            self.name, len(datalist))

                    self.logger.info("Merging data from BibTeX")
                    self.ctx.data.update(datalist[0])

        # try getting doi
        try:
            doi = self.get_doi()
        except NotImplementedError:
            pass
        else:
            if doi:
                self.ctx.data["doi"] = doi

    def fetch_files(self) -> None:
        # get documents
        try:
            self.download_document()
        except NotImplementedError:
            pass
        else:
            doc_rawdata = self.get_document_data()
            if doc_rawdata and self.check_document_format():
                import tempfile
                with tempfile.NamedTemporaryFile(
                        mode="wb+", delete=False) as f:
                    f.write(doc_rawdata)
                    self.logger.info("Saving downloaded file in '%s'", f.name)
                    self.ctx.files.append(f.name)

    def fetch(self) -> None:
        self.fetch_data()
        self.fetch_files()

    @classmethod
    def match(cls, url: str) -> Optional["Downloader"]:
        raise NotImplementedError(
            "Matching uri not implemented for this importer")

    def _get_body(self) -> bytes:
        """Get body of the uri, this is also important for unittesting"""
        return self.session.get(self.uri).content

    def _get_soup(self) -> "bs4.BeautifulSoup":
        """Get body of the uri, this is also important for unittesting"""
        if self._soup:
            return self._soup

        import bs4
        self._soup = bs4.BeautifulSoup(
            self._get_body(),
            features="html.parser" if sys.version_info.minor < 6 else "lxml")

        return self._soup

    def __str__(self) -> str:
        return "Downloader({0}, uri={1})".format(self.name, self.uri)

    def get_bibtex_url(self) -> Optional[str]:
        """It returns the urls that is to be access to download
        the bibtex information. It has to be implemented for every
        downloader, or otherwise it will raise an exception.

        :returns: Bibtex url
        """
        raise NotImplementedError(
            "Getting bibtex url not implemented for this downloader")

    def get_bibtex_data(self) -> Optional[str]:
        """Get the bibtex_data data if it has been downloaded already
        and if not download it and return the data in utf-8 format.

        :returns: Bibtex data in utf-8 format
        """
        if not self.bibtex_data:
            self.download_bibtex()
        return self.bibtex_data

    def download_bibtex(self) -> None:
        """Bibtex downloader, it should try to download bibtex information from
        the url provided by ``get_bibtex_url``.

        It sets the ``bibtex_data`` attribute if it succeeds.
        """
        url = self.get_bibtex_url()
        if not url:
            return
        res = self.session.get(url, cookies=self.cookies)
        self.logger.info("Downloading bibtex from '%s'", url)
        self.bibtex_data = res.content.decode()

    def get_document_url(self) -> Optional[str]:
        """It returns the urls that is to be access to download
        the document information. It has to be implemented for every
        downloader, or otherwise it will raise an exception.

        :returns: Document url
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
        """
        raise NotImplementedError(
            "Getting document url not implemented for this downloader")

    def get_document_data(self) -> Optional[bytes]:
        """Get the document_data data if it has been downloaded already
        and if not download it and return the data in binary format.

        :returns: Document data in binary format
        """
        if not self.document_data:
            self.download_document()
        return self.document_data

    def download_document(self) -> None:
        """Document downloader, it should try to download document information
        from the url provided by ``get_document_url``.

        It sets the ``document_data`` attribute if it succeeds.
        """
        url = self.get_document_url()
        if not url:
            return
        self.logger.info("Downloading file from '%s'", url)
        res = self.session.get(url, cookies=self.cookies)
        self.document_data = res.content

    def check_document_format(self) -> bool:
        """Check if the downloaded document has the filetype that the
        downloader expects. If the downloader does not expect any special
        filetype, accept anything because there is no way to know if it is
        correct.

        :returns: True if it is of the right type, else otherwise
        """
        def print_warning() -> None:
            self.logger.error(
                "The downloaded data does not seem to be of "
                "the correct type ('%s')",
                self.expected_document_extension)

        if self.expected_document_extension is None:
            return True

        import filetype
        retrieved_kind = filetype.guess(self.get_document_data())

        if retrieved_kind is None:
            print_warning()
            return False

        self.logger.debug(
            "Retrieved kind of document seems to be '%s'",
            retrieved_kind.mime)

        if isinstance(self.expected_document_extension, list):
            expected_document_extensions = self.expected_document_extension
        else:
            expected_document_extensions = [self.expected_document_extension]

        if retrieved_kind.extension in expected_document_extensions:
            return True
        else:
            print_warning()
            return False


def get_available_downloaders() -> List[Type[Downloader]]:
    """Get all declared downloader classes
    """
    _ret = papis.plugin.get_available_plugins(
        _extension_name())  # type: List[Type[Downloader]]
    return _ret


def get_matching_downloaders(url: str) -> Sequence[Downloader]:
    """Get matching downloaders sorted by their priorities.
    The first elements have the higher priority

    :param url: Url to be matched against
    :returns: A list of sorted downloaders
    """
    print(get_available_downloaders())
    _maybe_matches = [
        d.match(url)
        for d in get_available_downloaders()]  # List[Optional[Downloader]]
    matches = [m
               for m in _maybe_matches
               if m is not None]  # type: List[Downloader]
    print(matches)
    return sorted(
        matches,
        key=lambda k: k.priority,
        reverse=True)


def get_downloader_by_name(name: str) -> Type[Downloader]:
    """Get a downloader by its name

    :param name: Name of the downloader
    :returns: A downloader class
    """
    downloader_class = papis.plugin.get_extension_manager(
        _extension_name())[name].plugin  # type: Type[Downloader]
    return downloader_class


def get_info_from_url(
        url: str,
        expected_doc_format: Optional[str] = None
        ) -> papis.importer.Context:
    """Get information directly from url

    :param url: Url of the resource
    :param expected_doc_format: override the doc format of the document
    :returns: Context object
    """

    downloaders = get_matching_downloaders(url)
    if not downloaders:
        logger.warning("No matching downloader found for '%s'", url)
        return papis.importer.Context()

    logger.debug("Found %d matching downloaders", len(downloaders))
    downloader = downloaders[0]

    logger.info("Using downloader '%s'", downloader)
    if downloader.expected_document_extension is None and \
            expected_doc_format is not None:
        downloader.expected_document_extension = expected_doc_format
    downloader.fetch()
    return downloader.ctx
