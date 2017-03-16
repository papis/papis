import re
import urllib.request
import papis.downloaders.base


class Aps(papis.downloaders.base.Downloader):

    """Docstring for Aps. """

    def __init__(self, url):
        """TODO: to be defined1. """
        papis.downloaders.base.Downloader.__init__(self, url)

    @classmethod
    def match(cls, url):
        if re.match(r".*aps.org.*", url):
            return Aps(url)
        else:
            return False

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
