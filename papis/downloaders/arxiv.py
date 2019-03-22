import re
import os
import papis.downloaders.base
import arxiv2bib
import papis.arxiv


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(self, url, name="arxiv")
        self.expected_document_extension = 'pdf'
        arxivid = None

    @classmethod
    def match(cls, url):
        arxivid = papis.arxiv.find_arxivid_in_text(url)
        if arxivid:
            url = "https://arxiv.org/abs/{0}".format(arxivid)
            down = Downloader(url)
            down.arxivid = arxivid
            return down
        else:
            return False

    def get_identifier(self):
        """Get arxiv identifier
        :returns: Identifier
        """
        if not self.arxivid:
            self.arxivid = papis.arxiv.find_arxivid_in_text(self.get_url())
        return self.arxivid

    def get_bibtex_url(self):
        identifier = self.get_identifier()
        return identifier

    def download_bibtex(self):
        bib_url = self.get_bibtex_url()
        bibtexCli = arxiv2bib.Cli([bib_url])
        bibtexCli.run()
        self.logger.debug("[bibtex url] = %s" % bib_url)
        data = ''.join(bibtexCli.output).replace('\n', ' ')
        self.bibtex_data = data

    def get_document_url(self):
        # https://arxiv.org/pdf/1702.01590
        arxivid = self.get_identifier()
        self.logger.debug("arxivid %s" % arxivid)
        pdf_url = "https://arxiv.org/pdf/{arxivid}.pdf".format(arxivid=arxivid)
        self.logger.debug("[pdf url] = %s" % pdf_url)
        return pdf_url
