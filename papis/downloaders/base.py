import os
import logging
import urllib.request
import papis.config


class Downloader(object):

    """This is the base class for every downloader.
    """

    def __init__(self, url=""):
        self.url = url
        self.src = os.path.basename(__file__)
        self.logger = logging.getLogger("downloaders:"+self.src)
        self.bibtex_data = None
        self.document_data = None
        self.logger.debug("[url] = %s" % url)

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

    def getBibtexUrl(self):
        """It returns the urls that is to be access to download
        the bibtex information. It has to be implemented for every
        downloader, or otherwise it will raise an exception.

        :returns: Bibtex url
        :rtype:  str
        """
        raise NotImplementedError(
            "Getting bibtex url not implemented for this downloader"
        )

    def getBibtexData(self):
        """Get the bibtex_data data if it has been downloaded already
        and if not download it and return the data in utf-8 format.

        :returns: Bibtex data in utf-8 format
        :rtype:  str
        """
        if not self.bibtex_data:
            self.downloadBibtex()
        return self.bibtex_data

    def downloadBibtex(self):
        """Bibtex downloader, it should try to download bibtex information from
        the url provided by ``getBibtexUrl``.

        It sets the ``bibtex_data`` attribute if it succeeds.

        :returns: Nothing
        :rtype:  None
        """
        url = self.getBibtexUrl()
        if not url:
            return False
        data = urllib.request.urlopen(url)\
            .read()\
            .decode('utf-8')
        self.bibtex_data = data

    def getDocumentUrl(self):
        """It returns the urls that is to be access to download
        the document information. It has to be implemented for every
        downloader, or otherwise it will raise an exception.

        :returns: Document url
        :rtype:  str
        """
        raise NotImplementedError(
            "Getting bibtex url not implemented for this downloader"
        )

    def getDoi(self):
        """It returns the doi of the document, if it is retrievable.
        It has to be implemented for every downloader, or otherwise it will
        raise an exception.

        :returns: Document doi
        :rtype:  str
        """
        raise NotImplementedError(
            "Getting document url not implemented for this downloader"
        )

    def getDocumentData(self):
        """Get the document_data data if it has been downloaded already
        and if not download it and return the data in binary format.

        :returns: Document data in binary format
        :rtype:  str
        """
        if not self.document_data:
            self.downloadDocument()
        return self.document_data

    def downloadDocument(self):
        """Document downloader, it should try to download document information from
        the url provided by ``getDocumentUrl``.

        It sets the ``document_data`` attribute if it succeeds.

        :returns: Nothing
        :rtype:  None
        """
        self.logger.debug("Downloading document")
        url = self.getDocumentUrl()
        if not url:
            return False
        request = urllib.request.Request(
            url,
            headers={
                'User-Agent': papis.config.get('user-agent')
            }
        )
        data = urllib.request.urlopen(request).read()
        self.document_data = data

    def setUrl(self, url):
        """Url setter for Downloader

        :param url: String containing a valid url
        :type  url: str
        :returns: Downloader object
        """
        self.url = url
        return self

    def getUrl(self):
        """Url getter for Downloader
        :returns: Main url of the Downloader
        :rtype:  str
        """
        return self.url
