import re
import os
import papis.downloaders.base
import arxiv2bib


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(self, url)

    @classmethod
    def match(cls, url):
        # arXiv:1701.08223v2
        m = re.match(r"^arxiv:(.*)", url, re.IGNORECASE)
        if m:
            url = "https://arxiv.org/abs/{m}".format(m=m.group(1))
        if re.match(r".*arxiv.org.*", url):
            return Downloader(url)
        else:
            return False

    def get_identifier(self):
        """Get arxiv identifier
        :returns: Identifier
        """
        url = self.getUrl()
        return re.sub(r'^.*arxiv.org/(abs|pdf)/(.*)\/?$', r'\2', url)

    def getBibtexUrl(self):
        identifier = self.get_identifier()
        return identifier

    def downloadBibtex(self):
        bibtexCli = arxiv2bib.Cli([self.getBibtexUrl()])
        bibtexCli.run()
        data = os.linesep.join(bibtexCli.output)
        self.bibtex_data = data

    def getDocumentUrl(self):
        # https://arxiv.org/pdf/1702.01590
        url = self.getUrl()
        identifier = self.get_identifier()
        self.logger.debug("[paper id] = %s" % identifier)
        pdf_url = "https://arxiv.org/pdf/"+identifier+".pdf"
        self.logger.debug("[pdf url] = %s" % pdf_url)
        return pdf_url

# vim-run: python3 %
