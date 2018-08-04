import re
import urllib.parse
import urllib.request
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(self, url, name="ieee")
        self.expected_document_format = 'pdf'

    @classmethod
    def match(cls, url):
        m = re.match(r"^ieee:(.*)", url, re.IGNORECASE)
        if m:
            url = "http://ieeexplore.ieee.org/document/{m}".format(
                m=m.group(1)
            )
        if re.match(r".*ieee.org.*", url):
            # http://http://ieeexplore.ieee.org/document/7989161/
            url = re.sub(r"\.pdf.*$", "", url)
            return Downloader(url)
        else:
            return False

    def get_identifier(self):
        url = self.get_url()
        return re.sub(r'^.*ieeexplore.ieee.org/document/(.*)\/', r'\1', url)

    def get_bibtex_url(self):
        identifier = self.get_identifier()
        bibtex_url = \
            'http://ieeexplore.ieee.org/xpl/downloadCitations?reload=true'
        data = {
            'recordIds': identifier,
            'citations-format': 'citation-and-abstract',
            'download-format': 'download-bibtex',
            'x': '0',
            'y': '0'
        }
        return bibtex_url, data

    def download_bibtex(self):
        bib_url, values = self.get_bibtex_url()
        post_data = urllib.parse.urlencode(values)
        post_data = post_data.encode('ascii')

        self.logger.debug("[bibtex url] = %s" % bib_url)

        req = urllib.request.Request(bib_url, post_data)
        with urllib.request.urlopen(req) as response:
            data = response.read()
            text = data.decode('utf-8')
            text = text.replace('<br>', '')
            self.bibtex_data = text

    def get_document_url(self):
        identifier = self.get_identifier()
        self.logger.debug("[paper id] = %s" % identifier)
        pdf_url = "{}{}".format(
            "http://ieeexplore.ieee.org/"
            "stampPDF/getPDF.jsp?tp=&isnumber=&arnumber=",
            identifier
        )
        self.logger.debug("[pdf url] = %s" % pdf_url)
        return pdf_url
