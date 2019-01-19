import re
import papis.downloaders.base
import bs4


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(self, url, name="hal")
        self.expected_document_extension = 'pdf'

    @classmethod
    def match(cls, url):
        if re.match(r".*hal.*\.fr.*", url):
            return Downloader(url)
        else:
            return False

    def get_identifier(self):
        """
        >>> d = Downloader("http://www.hal.fr/2014TOU30305")
        >>> d.get_identifier()
        '2014TOU30305'
        >>> d = Downloader("http://www.hal.fr/2014TOU30305.bib/?asdf=2")
        >>> d.get_identifier()
        '2014TOU30305'
        """
        m = re.match(r".*hal.fr/([^/?.&]+).*", self.url)
        return m.group(1) if m is not None else None

    def get_document_url(self):
        """
        >>> d = Downloader("https://hal.archives-ouvertes.fr/jpa-00205888?asf=")
        >>> d.get_document_url()
        'https://hal.archives-ouvertes.fr/jpa-00205888/document'
        """
        url = re.sub(r'\?.*', '', self.get_url()) + '/document'
        return url

    def get_bibtex_url(self):
        """
        >>> d = Downloader("https://hal.archives-ouvertes.fr/jpa-00205888?asf=")
        >>> d.get_bibtex_url()
        'https://hal.archives-ouvertes.fr/jpa-00205888/bibtex'
        """
        url = re.sub(r'\?.*', '', self.get_url()) + '/bibtex'
        return url
