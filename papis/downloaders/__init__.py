import logging
import re
import aps.Aps

def getDownloader(url):
    """TODO: Docstring for getDownloader.

    :url: TODO
    :returns: TODO

    """
    if re.match(r".*aps.org.*", url):
        return aps.Aps

class Downloader(object):

    """Base class for downloaders"""

    def __init__(self, url=""):
        self.url = url
        self.type = self.__class__.__name__.lower()
        self.logger = logging.getLogger(self.type)
        self.bibtex_data = ""

    def getBibtexData(self):
        """TODO: Docstring for getBibtex.
        :returns: TODO

        """
        return self.bibtex_data
    def getBibtexUrl(self):
        pass
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
