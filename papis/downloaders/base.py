import os
import logging
import urllib.request


class Downloader(object):

    """Base class for downloaders"""

    def __init__(self, url=""):
        self.url = url
        self.src = os.path.basename(__file__)
        self.logger = logging.getLogger("downloaders:"+self.src)
        self.bibtex_data = None
        self.document_data = None
        self.logger.debug("[url] = %s" % url)

    @classmethod
    def match(url):
        return False

    def getBibtexUrl(self):
        pass

    def getBibtexData(self):
        if not self.bibtex_data:
            self.downloadBibtex()
        return self.bibtex_data

    def downloadBibtex(self):
        """Bibtex downloader, it should try to download bibtex information from
        the url
        :returns: TODO

        """
        url = self.getBibtexUrl()
        if not url:
            return False
        data = urllib.request.urlopen(url)\
            .read()\
            .decode('utf-8')
        self.bibtex_data = data

    def getDocumentUrl(self):
        pass

    def getDocumentData(self):
        if not self.document_data:
            self.downloadDocument()
        return self.document_data

    def downloadDocument(self):
        """Document downloader, it should try to download bibtex information
        from the url
        :returns: TODO

        """
        self.logger.debug("Downloading document")
        url = self.getDocumentUrl()
        if not url:
            return False
        data = urllib.request.urlopen(url).read()
        self.document_data = data

    def setUrl(self, url):
        """Url setter for Downloader

        :url: String containing a valid url
        :returns: Object

        """
        self.url = url
        return self

    def getUrl(self):
        """TODO: Url getter for Downloader
        :returns: url linked to the Downloader

        """
        return self.url
