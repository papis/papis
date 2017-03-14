import re
import os
import urllib.request
import papis.downloaders.base
import arxiv2bib


class Arxiv(papis.downloaders.base.Downloader):

    """Docstring for Aps. """

    def __init__(self, url):
        """TODO: to be defined1. """
        papis.downloaders.base.Downloader.__init__(self, url)

    @classmethod
    def match(cls, url):
        if re.match(r".*arxiv.org.*", url):
            return Arxiv(url)
        else:
            return False
    def getBibtexUrl(self):
        # https://arxiv.org/abs/1702.01590
        url = self.getUrl()
        burl = re.sub(r'.*arxiv.org.*/([0-9]+\.[0-9]+).*',r'\1', url)
        self.logger.debug("[paper id] = %s"%burl)
        return burl
    def downloadBibtex(self):
        """TODO: Docstring for downloadBibtex.

        :arg1: TODO
        :returns: TODO

        """
        bibtexCli = arxiv2bib.Cli([self.getBibtexUrl()])
        bibtexCli.run()
        data = os.linesep.join(bibtexCli.output)
        self.bibtex_data = data
    def downloadBibtex(self):
        """TODO: Docstring for downloadBibtex.

        :arg1: TODO
        :returns: TODO

        """
        bibtexCli = arxiv2bib.Cli([self.getBibtexUrl()])
        bibtexCli.run()
        data = os.linesep.join(bibtexCli.output)
        self.bibtex_data = data
    def getDocumentUrl(self):
        """TODO: Docstring for getDocumentUrl.
        :returns: TODO

        """
        # https://arxiv.org/pdf/1702.01590.pdf
        url = self.getUrl()
        burl = re.sub(r'.*arxiv.org.*/([0-9]+\.[0-9]+).*',r'\1', url)
        burl = "https://arxiv.org/pdf/"+burl+".pdf"
        self.logger.debug("[pdf url] = %s"%burl)
        return burl

#vim-run: python3 %
