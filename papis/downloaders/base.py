import re
import logging

class Downloader(object):

    """Base class for downloaders"""

    def __init__(self, url=""):
        self.url = url
        self.src = self.__class__.__name__.lower()
        self.logger = logging.getLogger("downloaders:"+self.src)
        self.bibtex_data = None
        self.logger.debug("[url] = %s"%url)

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
        pass
    def getDocumentUrl(self):
        pass
    def downloadDocument(self):
        """Document downloader, it should try to download bibtex information
        from the url
        :returns: TODO

        """
        pass
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
