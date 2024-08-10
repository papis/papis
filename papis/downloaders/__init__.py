import re
import os
import tempfile
from typing import List, Optional, Any, Sequence, Type, Dict, Union, TYPE_CHECKING

import papis.config
import papis.document
import papis.importer
import papis.plugin
import papis.utils
import papis.logging

if TYPE_CHECKING:
    import bs4

logger = papis.logging.get_logger(__name__)

DOWNLOADERS_EXTENSION_NAME = "papis.downloader"


class Importer(papis.importer.Importer):
    """Importer that tries to get data and files from implemented downloaders.

    This importer simply calls :func:`get_info_from_url` on the given URI.
    """

    def __init__(self, uri: str = "") -> None:
        super().__init__(uri=uri, name="url")

    @classmethod
    def match(cls, uri: str) -> Optional[papis.importer.Importer]:
        return (
            Importer(uri=uri)
            if re.match(" *http(s)?.*", uri) is not None
            else None
        )

    @papis.importer.cache
    def fetch(self) -> None:
        self.logger.info("Attempting to import from URL '%s'.", self.uri)
        self.ctx = get_info_from_url(self.uri)

    def fetch_data(self) -> None:
        self.fetch()

    def fetch_files(self) -> None:
        self.fetch()


class Downloader(papis.importer.Importer):
    """A base class for downloader instances implementing common functionality.

    In general, downloaders are expected to implement a subset of the methods
    below, depending on the generality. A simple downloader could only
    implement :meth:`get_bibtex_url` and :meth:`get_document_url`.

    .. attribute:: expected_document_extension

        A single extension or a list of extensions supported by the downloader.
        The extensions do not contain the leading dot, e.g. ``["pdf", "djvu"]``.

    .. attribute:: priority

        A priority given to the downloader. This is used when trying to
        automatically determine a preferred downloader for a given URL.

    .. attribute:: session

        A :class:`requests.Session` that is used for all the requests made by
        the downloader.
    """

    def __init__(self,
                 uri: str = "",
                 name: str = "",
                 ctx: Optional[papis.importer.Context] = None,
                 expected_document_extension: Optional[
                     Union[str, Sequence[str]]] = None,
                 cookies: Optional[Dict[str, str]] = None,
                 priority: int = 1,
                 ) -> None:
        if isinstance(expected_document_extension, str):
            expected_document_extension = (expected_document_extension,)

        if expected_document_extension is not None:
            expected_document_extension = tuple(expected_document_extension)

        if cookies is None:
            cookies = {}

        super().__init__(uri=uri, name=name, ctx=ctx)
        self.logger = papis.logging.get_logger(f"papis.downloader.{self.name}")

        self.expected_document_extensions = expected_document_extension
        self.priority = priority
        self.cookies = cookies
        self.session = papis.utils.get_session()

        # NOTE: used to cache data
        self._soup: Optional[bs4.BeautifulSoup] = None
        self.bibtex_data: Optional[str] = None
        self.document_data: Optional[bytes] = None
        self.document_extension: Optional[str] = None

    def __del__(self) -> None:
        self.session.close()

    @classmethod
    def match(cls, url: str) -> Optional["Downloader"]:
        """Check if the downloader can process the given URL.

        For example, an importer that supports links from the arXiv can check
        that the given URL matches using:

        .. code:: python

            re.match(r".*arxiv.org.*", uri)

        This can then be used to instantiate and return a corresponding
        :class:`Downloader` object.

        :param url: An URL where the document information should be retrieved from.
        :return: A downloader instance if the match to the URL is successful or
            *None* otherwise.
        """
        raise NotImplementedError(
            f"Matching URI not implemented for '{cls.__module__}.{cls.__name__}'"
            )

    @papis.importer.cache
    def fetch(self) -> None:
        """Fetch metadata and files for the given :attr:`~papis.importer.Importer.uri`.

        This method calls :meth:`Downloader.fetch_data` and
        :meth:`Downloader.fetch_files` to get all the information available for
        the document. It is recommended to implement the two methods separately,
        if possible, for maximum flexibility.

        The imported data is stored in :attr:`~papis.importer.Importer.ctx` and
        it is not queried again on subsequent calls to this function.
        """
        self.fetch_data()
        self.fetch_files()

    def fetch_data(self) -> None:
        """Fetch metadata for the given URL.

        The imported metadata is stored in :attr:`~papis.importer.Importer.ctx`.
        To fetch the metadata, the following steps are followed

        * Call :meth:`get_data` to import any scraped metadata.
        * Call :meth:`get_bibtex_data` to import any metadata from BibTeX
          files available remotely.

        Note that previous steps overwrite any information, i.e. the BibTeX
        data will take priority.
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
                import papis.bibtex
                datalist = papis.bibtex.bibtex_to_dict(bib_rawdata)
                if datalist:
                    if len(datalist) > 1:
                        self.logger.warning(
                            "'%s' found %d BibTeX entries. Picking the first one!",
                            self.name, len(datalist))

                    self.logger.info("Merging data from BibTeX.")
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
        """Fetch files from the given :attr:`~papis.importer.Importer.uri`.

        The imported files are stored in :attr:`~papis.importer.Importer.ctx`.
        The file is downloaded with :meth:`download_document` and stored as
        a temporary file.
        """
        # get documents
        try:
            self.download_document()
        except NotImplementedError:
            pass
        else:
            doc_rawdata = self.get_document_data()
            if doc_rawdata and self.check_document_format():
                extension = self.get_document_extension()
                if extension:
                    extension = f".{extension}"

                with tempfile.NamedTemporaryFile(
                        mode="wb+", delete=False,
                        suffix=extension) as f:
                    f.write(doc_rawdata)
                    self.logger.info("Saving downloaded file in '%s'.", f.name)
                    self.ctx.files.append(f.name)

    def _get_body(self) -> bytes:
        """Download the content (body) at the given URL.

        This method is mainly available for unittesting, i.e. so that it can get
        monkeypatched and return known data.
        """
        return self.session.get(self.uri, cookies=self.cookies).content

    def _get_soup(self) -> "bs4.BeautifulSoup":
        """Create an instance of :class:`bs4.BeautifulSoup` that parses
        the results from :meth:`_get_body`.
        """
        if self._soup:
            return self._soup

        import bs4
        self._soup = bs4.BeautifulSoup(self._get_body(), features="lxml")

        return self._soup

    def __str__(self) -> str:
        return f"Downloader({self.name}, uri={self.uri})"

    def get_bibtex_url(self) -> Optional[str]:
        """
        :returns: an URL to a valid BibTeX file that can be used to extract
            metadata about the document.
        """
        raise NotImplementedError(
            f"Getting a BibTeX URL not implemented for the '{self.name}' downloader")

    def get_bibtex_data(self) -> Optional[str]:
        """Get BibTeX data available at :meth:`get_bibtex_url`, if any.

        :returns: a string containing the BibTeX data, which can be parsed.
        """
        if not self.bibtex_data:
            self.download_bibtex()

        return self.bibtex_data

    def download_bibtex(self) -> None:
        """Download and store that BibTeX data from :meth:`get_bibtex_url`.

        Use :meth:`get_bibtex_data` to access the metadata from the BibTeX URL.
        """
        url = self.get_bibtex_url()
        if not url:
            return
        self.logger.info("Downloading BibTeX from '%s'.", url)

        response = self.session.get(url, cookies=self.cookies)
        self.bibtex_data = response.content.decode()

    def get_data(self) -> Dict[str, Any]:
        """Retrieve general metadata from the given URL.

        This function is meant to be as general as possible and should not
        contain data imported from BibTeX (use :meth:`get_bibtex_data` instead).
        For example, this can be used for web scrapping or calling other website
        APIs to gather metadata about the document.
        """
        raise NotImplementedError(
            f"Getting data is not implemented for the '{self.name}' downloader"
            )

    def get_doi(self) -> Optional[str]:
        """
        :returns: a DOI for the document, if any.
        """
        raise NotImplementedError(
            f"Getting the DOI not implemented for the '{self.name}' downloader"
            )

    def get_document_url(self) -> Optional[str]:
        """
        :returns: a URL to a file that should be downloaded.
        """
        raise NotImplementedError(
            f"Getting a document URL not implemented for the '{self.name}' downloader"
            )

    def get_document_data(self) -> Optional[bytes]:
        """Get data for the downloaded file that is given by :meth:`get_document_url`.

        :returns: the bytes (stored in memory) for the downloaded file.
        """
        if not self.document_data:
            self.download_document()

        return self.document_data

    def get_document_extension(self) -> str:
        """
        :returns: a guess for the extension of :meth:`get_document_data`. This
            is based on `filetype <https://h2non.github.io/filetype.py/>`__ and
            uses magic file signatures to determine the type. If no guess is valid,
            an empty string is returned.
        """
        if self.document_extension is None:
            data = self.get_document_data()
            document_extension = None
            if data is not None:
                from papis.filetype import guess_content_extension
                document_extension = guess_content_extension(data)

            self.document_extension = (
                document_extension if document_extension is not None else ""
            )

        return self.document_extension

    def download_document(self) -> None:
        """Download and store the file that is given by :meth:`get_document_url`.

        Use :meth:`get_document_data` to access the file binary contents.
        """
        url = self.get_document_url()
        if not url:
            return
        self.logger.info("Downloading file from '%s'.", url)

        response = self.session.get(url, cookies=self.cookies)
        self.document_data = response.content

    def check_document_format(self) -> bool:
        """Check if the document downloaded by :meth:`download_document` has
        a file type supported by the downloader.

        If the downloader has no preferred type, then all files are accepted.

        :returns: *True* if the document has a supported file type and *False*
            otherwise.
        """
        if self.expected_document_extensions is None:
            return True

        extension = self.get_document_extension()
        if extension and extension in self.expected_document_extensions:
            return True
        else:
            self.logger.error(
                "The downloaded data does not seem to be of "
                "the expected types: '%s'",
                "', '".join(self.expected_document_extensions))
            return False


def get_available_downloaders() -> List[Type[Downloader]]:
    """Get all declared downloader classes."""
    return papis.plugin.get_available_plugins(DOWNLOADERS_EXTENSION_NAME)


def get_matching_downloaders(url: str) -> List[Downloader]:
    """Get downloaders matching the given *url*.

    :param url: a URL to match.
    :returns: a list of downloaders (sorted by priority).
    """
    available_downloaders = get_available_downloaders()
    logger.debug("Found available downloaders: '%s'.",
                 "', '".join([d.__module__ for d in available_downloaders]))

    matches = [d
               for maybe_downloader in available_downloaders
               for d in [maybe_downloader.match(url)]
               if d is not None]  # List[Downloader]

    logger.debug("Found downloaders matching query '%s': '%s'.",
                 url, "', '".join([d.name for d in matches]))

    return sorted(matches, key=lambda d: d.priority, reverse=True)


def get_downloader_by_name(name: str) -> Type[Downloader]:
    """Get a specific downloader by its name.

    :param name: the name of the downloader. Note that this is the name of
        the entry point used to define the downloader. In general, this should
        be the same as its name, but this is not enforced.
    :returns: a downloader class.
    """
    downloader_class: Type[Downloader] = (
        papis.plugin.get_extension_manager(DOWNLOADERS_EXTENSION_NAME)[name].plugin
    )
    return downloader_class


def get_info_from_url(
        url: str,
        expected_doc_format: Optional[str] = None
        ) -> papis.importer.Context:
    """Get information directly from the given *url*.

    :param url: the URL of a resource.
    :param expected_doc_format: an expected document file type, that is used to
        override the file type defined by the chosen downloader.
    """

    downloaders = get_matching_downloaders(url)
    if not downloaders:
        logger.warning("No matching downloader found for '%s'.", url)
        return papis.importer.Context()

    logger.debug("Found %d matching downloaders.", len(downloaders))

    down = downloaders[0]
    logger.info("Using downloader '%s'.", down)

    if (
            down.expected_document_extensions is None
            and expected_doc_format is not None):
        down.expected_document_extensions = (expected_doc_format,)

    down.fetch()
    return down.ctx


def download_document(
        url: str,
        expected_document_extension: Optional[str] = None,
        cookies: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None,
        ) -> Optional[str]:
    """Download a document from *url* and store it in a local file.

    An appropriate filename is deduced from the HTTP response in most cases.
    If this is not possible, a temporary file is created instead. To ensure that
    the desired filename is chosen, provide the *filename* argument instead.

    :param url: the URL of a remote file.
    :param expected_document_extension: an expected file extension. If *None*, then
        an extension is guessed from the file contents or from the *filename*.
    :param filename: a file name for the document, regardless of the given URL and
        extension.

    :returns: an absolute path to a local file containing the data from *url*.
    """
    if cookies is None:
        cookies = {}

    try:
        with papis.utils.get_session() as session:
            response = session.get(url, cookies=cookies, allow_redirects=True)
    except Exception as exc:
        logger.error("Failed to fetch '%s'.", url, exc_info=exc)
        return None

    if not response.ok:
        logger.error("Could not download document '%s'. (HTTP status: %s %d).",
                     url, response.reason, response.status_code)
        return None

    # NOTE: we can guess the filename from the response headers
    #   Content-Disposition: inline; filename="some_file_name.ext"
    #   Content-Disposition: attachement; filename="some_file_name.ext"
    key = "Content-Disposition"
    if not filename and key in response.headers:
        from email.message import EmailMessage

        msg = EmailMessage()
        msg[key] = response.headers[key]
        filename = msg.get_filename()

    key = "Content-Type"
    if not filename and key in response.headers:
        from email.message import EmailMessage

        msg = EmailMessage()
        msg[key] = response.headers[key]

        from mimetypes import guess_extension

        ext = guess_extension(msg.get_content_type())

        from urllib.parse import urlsplit

        result = urlsplit(url)
        if result.path.strip("/"):
            basename = os.path.basename(result.path)
        else:
            basename = result.netloc
        filename = f"{basename}{ext}"

    # try go guess an extension
    ext = expected_document_extension
    if ext is None:
        if filename is None:
            from papis.filetype import guess_content_extension
            ext = guess_content_extension(response.content)
            ext = f".{ext}"
        else:
            _, ext = os.path.splitext(filename)
    else:
        if not ext.startswith("."):
            ext = f".{ext}"

    # write out the file contents
    if filename:
        root, _ = os.path.splitext(os.path.basename(filename))
        outfile = os.path.join(tempfile.gettempdir(), f"{root}{ext}")

        with open(outfile, mode="wb") as f:
            f.write(response.content)
    else:
        with tempfile.NamedTemporaryFile(
                mode="wb+",
                suffix=f"{ext}",
                delete=False) as f:
            f.write(response.content)
            outfile = f.name

    return outfile
