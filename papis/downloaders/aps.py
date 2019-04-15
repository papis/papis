import re
import papis.downloaders.fallback


class Downloader(papis.downloaders.fallback.Downloader):

    def __init__(self, url):
        papis.downloaders.fallback.Downloader.__init__(self, url, name="aps")
        self.expected_document_extension = 'pdf'
        self.priority = 10

    @classmethod
    def match(cls, url):
        if re.match(r".*aps.org.*", url):
            return Downloader(url)
        else:
            return False

    def get_bibtex_url(self):
        url = self.uri
        burl = re.sub(r'/abstract', r'/export', url)\
            + "?type=bibtex&download=true"
        self.logger.debug("[bibtex url] = %s" % burl)
        return burl
