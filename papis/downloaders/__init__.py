

class Downloader(object):

    """Base class for downloaders"""

    def __init__(self):
        self.url = ""

    def getBibtex(self):
        """TODO: Docstring for getBibtex.
        :returns: TODO

        """
        pass
    def downloadBibtex(self):
        """Bibtex downloader, it should try to download bibtex information from
        the url
        :returns: TODO

        """
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
