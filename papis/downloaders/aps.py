import re
import urllib.request
import papis.downloaders.base


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(self, url, name="aps")
        self.expected_document_extension = 'pdf'

    @classmethod
    def match(cls, url):
        if re.match(r".*aps.org.*", url):
            return Downloader(url)
        else:
            return False

    def get_document_url(self):
        # http://whatever.aps.org/whatever/whatever/10.1103/PhysRevLett.115.066402
        # https://journals.aps.org/prl/pdf/10.1103/PhysRevLett.119.030403
        url = self.get_url()
        burl = re.sub(r'(aps.org/[a-z]+)/([a-z]+)', r'\1/pdf', url)
        self.logger.debug("[document url] = %s" % burl)
        return burl

    def get_doi(self):
        # http://whatever.aps.org/whatever/whatever/(10.1103/PhysRevLett.115.066402)
        url = self.get_url()
        burl = re.sub(r'.*(aps.org/[a-z]+/[a-z]+/)', r'', url)
        self.logger.debug("[document doi] = %s" % burl)
        return burl

    def get_bibtex_url(self):
        # http://journals.aps.org/prl/export/10.1103/
        # PhysRevLett.115.066402?type=bibtex&download=true
        # http://journals.aps.org/prl/abstract/10.1103/PhysRevLett.115.066402
        url = self.get_url()
        burl = re.sub(r'/abstract', r'/export', url)\
            + "?type=bibtex&download=true"
        self.logger.debug("[bibtex url] = %s" % burl)
        return burl
