import re
from typing import Optional

import papis.downloaders.base


class Downloader(papis.downloaders.Downloader):

    def __init__(self, url: str) -> None:
        super().__init__(url, name="thesesfr", expected_document_extension="pdf")

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        if re.match(r".*theses.fr.*", url):
            return Downloader(url)
        else:
            return None

    def get_identifier(self) -> Optional[str]:
        """
        >>> d = Downloader("https://www.theses.fr/2014TOU30305")
        >>> d.get_identifier()
        '2014TOU30305'
        >>> d = Downloader("https://www.theses.fr/2014TOU30305.bib/?asdf=2")
        >>> d.get_identifier()
        '2014TOU30305'
        """
        m = re.match(r".*theses.fr/([^/?.&]+).*", self.uri)
        return m.group(1) if m is not None else None

    def get_document_url(self) -> Optional[str]:
        """
        >>> d = Downloader("https://www.theses.fr/2014TOU30305")
        >>> d.get_document_url()
        'https://thesesups.ups-tlse.fr/2722/1/2014TOU30305.pdf'
        >>> d = Downloader("https://theses.fr/1998ENPC9815")
        >>> d.get_document_url()
        'https://pastel.archives-ouvertes.fr/tel-00005590v2/file/Cances.pdf'
        """
        import bs4

        # TODO: Simplify this function for typing
        raw_data = self.session.get(self.uri).content.decode("utf-8")
        soup = bs4.BeautifulSoup(raw_data, "html.parser")
        a = list(filter(
            lambda t: re.match(r".*en ligne.*", t.text),
            soup.find_all("a")
        ))

        if not a:
            self.logger.error("No document found for '%s'.", self.uri)
            return None

        second_url = a[0]["href"]
        raw_data = self.session.get(second_url).content.decode("utf-8")
        soup = bs4.BeautifulSoup(raw_data, "html.parser")
        a = list(filter(
            lambda t: re.match(r".*pdf$", t.get("href", "")),
            soup.find_all("a")
        ))

        if not a:
            self.logger.error("No document found for '%s'.", second_url)
            return None

        return str(a[0]["href"])

    def get_bibtex_url(self) -> Optional[str]:
        """
        >>> d = Downloader("https://www.theses.fr/2014TOU30305")
        >>> d.get_bibtex_url()
        'https://www.theses.fr/2014TOU30305.bib'
        """
        url = "https://www.theses.fr/{id}.bib".format(id=self.get_identifier())
        self.logger.debug("Using BibTeX URL: '%s'.", url)
        return url
