import re
import urllib.request
import papis.downloaders


class Aps(papis.downloaders.Downloader):

    """Docstring for Aps. """

    def __init__(self, url):
        """TODO: to be defined1. """
        Downloader.__init__(self, url)

    def getBibtexUrl(self):
        # http://journals.aps.org/prl/export/10.1103/
        # PhysRevLett.115.066402?type=bibtex&download=true
        # http://journals.aps.org/prl/abstract/10.1103/PhysRevLett.115.066402
        url = self.getUrl()
        burl = re.sub(r"org/prl/abstract","org/prl/export", url)\
                +"?type=bibtex&download=true"
        self.logger.debug("Bibtex url %s"%burl)
        return burl
    def downloadBibtex(self, arg1):
        """TODO: Docstring for downloadBibtex.

        :arg1: TODO
        :returns: TODO

        """
        data = urllib.request.urlopen(self.getBibtexUrl()).read().decode('utf-8')
        self.bibtex_data = data
