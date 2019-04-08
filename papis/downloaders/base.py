import os
import logging
import requests
import papis.config
import papis.utils
import filetype
import papis.importer
import papis.bibtex
import tempfile


class Downloader(papis.importer.Importer):

    """This is the base class for every downloader.
    """

    def __init__(self, uri="", name="", ctx=papis.importer.Context()):
        assert(isinstance(uri, str))
        assert(isinstance(name, str))
        assert(isinstance(ctx, papis.importer.Context))
        self.uri = uri
        self.name = name or os.path.basename(__file__)
        self.ctx = ctx
        self.logger = logging.getLogger("downloader:"+self.name)
        self.logger.debug("uri {0}".format(uri))
        self.expected_document_extension = None
        self.priority = 1

        self.bibtex_data = None
        self.document_data = None

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

    def fetch(self):
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
                    self.ctx.data.update(datalist[0])

        # Try with get_data
        try:
            data = self.get_data()
            assert(isinstance(data, dict))
        except NotImplementedError:
            pass
        else:
            self.ctx.data.update(data)

        # try getting doi
        try:
            doi = self.get_doi()
        except NotImplementedError:
            pass
        else:
            self.ctx.data['doi'] = doi

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

    def __str__(self):
        return 'Downloader({0}, uri={1})'.format(self.name, self.uri)

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
        self.logger.info("downloading bibtex from {0}".format(url))
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

    def get_data(self):
        """A general data retriever, for instance when data needn't need
        to come from a bibtex
        """
        raise NotImplementedError(
            "Getting general data is not implemented for this downloader"
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
        url = self.get_document_url()
        if not url:
            return False
        self.logger.info("downloading file from {0}".format(url))
        res = self.session.get(url, cookies=self.cookies)
        self.document_data = res.content

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

        retrieved_kind = filetype.guess(self.get_document_data())

        if retrieved_kind is None:
            print_warning()
            return False

        self.logger.debug(
            'retrieved kind of document seems to be {0}'.format(
                retrieved_kind.mime)
        )

        if not isinstance(self.expected_document_extension, list):
            expected_document_extensions = [
                self.expected_document_extension
            ]

        if retrieved_kind.extension in expected_document_extensions:
            return True
        else:
            print_warning()
            return False
