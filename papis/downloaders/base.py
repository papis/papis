import re
import os
import logging
import requests
import papis.config
import papis.utils
import filetype


class Downloader(object):

    """This is the base class for every downloader.
    """

    def __init__(self, url="", name=""):
        self.url = url
        self.name = name or os.path.basename(__file__)
        self.logger = logging.getLogger("downloaders:"+self.name)
        self.bibtex_data = None
        self.document_data = None
        self.logger.debug("[url] = %s" % url)
        self.expected_document_extension = None

        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': papis.config.get('user-agent')
        }
        proxy = papis.config.get('downloader-proxy')
        if proxy is not None:
            self.session.proxies = {
                'http': proxy,
                'https': proxy,
            }
        self.cookies = {}

    def __repr__(self):
        return self.name

    @classmethod
    def match(url):
        """This method should be called to know if a given url matches
        the downloader or not.

        For example, a valid match for archive would be:
        .. code:: python

            return re.match(r".*arxiv.org.*", url)

        it will return something that is true if it matches and something
        falsely otherwise.

        :param url: Url where the document should be retrieved from.
        :type  url: str
        """
        raise NotImplementedError(
            "Matching url not implemented for this downloader"
        )

    def get_bibtex_url(self):
        """It returns the urls that is to be access to download
        the bibtex information. It has to be implemented for every
        downloader, or otherwise it will raise an exception.

        :returns: Bibtex url
        :rtype:  str
        """
        raise NotImplementedError(
            "Getting bibtex url not implemented for this downloader"
        )

    def get_bibtex_data(self):
        """Get the bibtex_data data if it has been downloaded already
        and if not download it and return the data in utf-8 format.

        :returns: Bibtex data in utf-8 format
        :rtype:  str
        """
        if not self.bibtex_data:
            self.download_bibtex()
        return self.bibtex_data

    def download_bibtex(self):
        """Bibtex downloader, it should try to download bibtex information from
        the url provided by ``get_bibtex_url``.

        It sets the ``bibtex_data`` attribute if it succeeds.

        :returns: Nothing
        :rtype:  None
        """
        url = self.get_bibtex_url()
        if not url:
            return False
        res = self.session.get(url, cookies=self.cookies)
        self.bibtex_data = res.content.decode()

    def get_document_url(self):
        """It returns the urls that is to be access to download
        the document information. It has to be implemented for every
        downloader, or otherwise it will raise an exception.

        :returns: Document url
        :rtype:  str
        """
        raise NotImplementedError(
            "Getting bibtex url not implemented for this downloader"
        )

    def get_doi(self):
        """It returns the doi of the document, if it is retrievable.
        It has to be implemented for every downloader, or otherwise it will
        raise an exception.

        :returns: Document doi
        :rtype:  str
        """
        raise NotImplementedError(
            "Getting document url not implemented for this downloader"
        )

    def get_document_data(self):
        """Get the document_data data if it has been downloaded already
        and if not download it and return the data in binary format.

        :returns: Document data in binary format
        :rtype:  str
        """
        if not self.document_data:
            self.download_document()
        return self.document_data

    def download_document(self):
        """Document downloader, it should try to download document information from
        the url provided by ``get_document_url``.

        It sets the ``document_data`` attribute if it succeeds.

        :returns: Nothing
        :rtype:  None
        """
        self.logger.debug("Downloading document")
        url = self.get_document_url()
        if not url:
            return False
        res = self.session.get(url, cookies=self.cookies)
        self.document_data = res.content

    def get_url(self):
        """Url getter for Downloader
        :returns: Main url of the Downloader
        :rtype:  str
        """
        return self.url

    def check_document_format(self):
        """Check if the downloaded document has the filetype that the
        downloader expects. If the downloader does not expect any special
        filetype, accept anything because there is no way to know if it is
        correct.

        :returns: True if it is of the right type, else otherwise
        :rtype:  bool
        """
        def print_warning():
            self.logger.error(
                "The downloaded data does not seem to be of"
                "the correct type (%s)" % self.expected_document_extension
            )

        if self.expected_document_extension is None:
            return True

        result = None
        kind = filetype.guess(self.get_document_data())

        if kind is None:
            print_warning()
            return False

        if not isinstance(self.expected_document_extension, list):
            self.expected_document_extension = [
                self.expected_document_extension]

        for expected_document_extension in self.expected_document_extension:

            expected_kind = filetype.get_type(ext=expected_document_extension)
            if expected_kind is None:
                raise Exception(
                    "I can't understand the expected extension {0}".format(
                        expected_document_extension
                    )
                )

            result = kind.mime == expected_kind.mime

        if not result:
            print_warning()

        return result
