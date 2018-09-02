import re
import os
import papis.downloaders.base
import arxiv2bib


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(self, url, name="arxiv")
        self.expected_document_extension = 'pdf'

    @classmethod
    def match(cls, url):
        m = re.match(r"^arxiv:(.*)", url, re.IGNORECASE)
        if m:
            url = "https://arxiv.org/abs/{m}".format(m=m.group(1))
        if re.match(r".*arxiv.org.*", url):
            # https://arxiv.org/pdf/1707.09820|.pdf?blahslas=sdfad|
            url = re.sub(r"\.pdf.*$", "", url)
            return Downloader(url)
        else:
            return False

    def get_identifier(self):
        """Get arxiv identifier
        :returns: Identifier
        """
        url = self.get_url()
        return re.sub(r'^.*arxiv.org/(abs|pdf)/(.*)\/?$', r'\2', url)

    def get_bibtex_url(self):
        identifier = self.get_identifier()
        return identifier

    def download_bibtex(self):
        bib_url = self.get_bibtex_url()
        bibtexCli = arxiv2bib.Cli([bib_url])
        bibtexCli.run()
        self.logger.debug("[bibtex url] = %s" % bib_url)
        data = os.linesep.join(bibtexCli.output)
        self.bibtex_data = data

    def get_document_url(self):
        # https://arxiv.org/pdf/1702.01590
        identifier = self.get_identifier()
        self.logger.debug("[paper id] = %s" % identifier)
        pdf_url = "https://arxiv.org/pdf/"+identifier+".pdf"
        self.logger.debug("[pdf url] = %s" % pdf_url)
        return pdf_url
