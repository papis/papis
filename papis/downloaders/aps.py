import re
import urllib.request
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    """Docstring for Aps. """

    def __init__(self, url):
        """TODO: to be defined1. """
        papis.downloaders.base.Downloader.__init__(self, url)

    @classmethod
    def match(cls, url):
        if re.match(r".*aps.org.*", url):
            return Downloader(url)
        else:
            return False

    def getDocumentUrl(self):
        # http://whatever.aps.org/whatever/whatever/10.1103/PhysRevLett.115.066402
        # https://journals.aps.org/prl/pdf/10.1103/PhysRevLett.119.030403
        url = self.getUrl()
        burl = re.sub(r'(aps.org/[a-z]+)/([a-z]+)', r'\1/pdf', url)
        self.logger.debug("[document url] = %s" % burl)
        return burl

    def getDoi(self):
        # http://whatever.aps.org/whatever/whatever/(10.1103/PhysRevLett.115.066402)
        url = self.getUrl()
        burl = re.sub(r'.*(aps.org/[a-z]+/[a-z]+/)', r'', url)
        self.logger.debug("[document doi] = %s" % burl)
        return burl

    def getBibtexUrl(self):
        # http://journals.aps.org/prl/export/10.1103/
        # PhysRevLett.115.066402?type=bibtex&download=true
        # http://journals.aps.org/prl/abstract/10.1103/PhysRevLett.115.066402
        url = self.getUrl()
        burl = re.sub(r'(aps.org/[a-z]+)/abstract', r'\1/export', url)\
            + "?type=bibtex&download=true"
        self.logger.debug("[bibtex url] = %s" % burl)
        return burl

    def downloadBibtex(self):
        """TODO: Docstring for downloadBibtex.

        :arg1: TODO
        :returns: TODO

        """
        data = urllib.request.urlopen(self.getBibtexUrl())\
            .read()\
            .decode('utf-8')
        self.bibtex_data = data

# vim-run: python3 %
