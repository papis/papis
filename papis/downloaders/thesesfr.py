import re
import papis.downloaders.base
import bs4


class Downloader(papis.downloaders.base.Downloader):

    def __init__(self, url):
        papis.downloaders.base.Downloader.__init__(self, url, name="thesesfr")
        self.expected_document_extension = 'pdf'

    @classmethod
    def match(cls, url):
        if re.match(r".*theses.fr.*", url):
            return Downloader(url)
        else:
            return False

    def get_identifier(self):
        """
        >>> d = Downloader("http://www.theses.fr/2014TOU30305")
        >>> d.get_identifier()
        '2014TOU30305'
        >>> d = Downloader("http://www.theses.fr/2014TOU30305.bib/?asdf=2")
        >>> d.get_identifier()
        '2014TOU30305'
        """
        m = re.match(r".*theses.fr/([^/?.&]+).*", self.url)
        return m.group(1) if m is not None else None

    def get_document_url(self):
        """
        >>> d = Downloader("http://www.theses.fr/2014TOU30305")
        >>> d.get_document_url()
        'http://thesesups.ups-tlse.fr/2722/1/2014TOU30305.pdf'
        >>> d = Downloader("http://theses.fr/1998ENPC9815")
        >>> d.get_document_url()
        """
        raw_data = self.session.get(self.url).content.decode('utf-8')
        soup = bs4.BeautifulSoup(raw_data, "html.parser")
        a = list(filter(
            lambda t: re.match(r'.*en ligne.*', t.text),
            soup.find_all('a')
        ))

        if not a:
            self.logger.error('No document url in theses.fr')
            return None

        second_url = a[0]['href']
        raw_data = self.session.get(second_url).content.decode('utf-8')
        soup = bs4.BeautifulSoup(raw_data, "html.parser")
        a = list(filter(
            lambda t: re.match(r'.*pdf$', t['href']),
            soup.find_all('a')
        ))

        if not a:
            self.logger.error('No document url in {0}'.format(second_url))
            return None

        return a[0]['href']

    def get_bibtex_url(self):
        """
        >>> d = Downloader("http://www.theses.fr/2014TOU30305")
        >>> d.get_bibtex_url()
        'http://www.theses.fr/2014TOU30305.bib'
        """
        url = "http://www.theses.fr/{id}.bib".format(id=self.get_identifier())
        self.logger.debug("[bibtex url] = %s" % url)
        return url

