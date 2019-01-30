import re
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):
    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(self, url, name="get")

    @classmethod
    def match(cls, url):
        """
        >>> Downloader.match('http://wha2341!@#!@$%!@#file.pdf') is False
        False
        >>> Downloader.match('https://whateverpt?is?therefile.epub') is False
        False
        >>> not Downloader.match('http://whatever?path?is?therefile')
        True
        """
        endings = "pdf|djvu|epub|mobi|jpg|png|md"
        m = re.match(r"^http.*\.(%s)$" % endings, url, re.IGNORECASE)
        if m:
            d = Downloader(url)
            d.expected_document_extension = m.group(1)
            return d
        else:
            return False

    def get_document_url(self):
        return self.get_url()
