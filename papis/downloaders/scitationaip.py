import re
import urllib.request
import papis.downloaders.base


class ScitationAip(papis.downloaders.base.Downloader):

    """Docstring for Aps. """

    def __init__(self, url):
        """TODO: to be defined1. """
        papis.downloaders.base.Downloader.__init__(self, url)

    @classmethod
    def match(cls, url):
        if re.match(r".*aip.scitation.org.*", url):
            return ScitationAip(url)
        else:
            return False
    def getDocumentUrl(self):
        # http://aip.scitation.org/doi/pdf/10.1063/1.4873138
        url = self.getUrl()
        durl = re.sub(r'(scitation.org/doi)/[a-z]+/(.*)',r'\1/pdf/\2', url)
        self.logger.debug("[doc url] = %s"%durl)
        return durl
    def getBibtexUrl(self):
        # http://aip.scitation.org/doi/export/10.1063/1.4873138
        pass

#vim-run: python3 %
