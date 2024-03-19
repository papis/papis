import re
from typing import Optional

import papis.downloaders.base


class Downloader(papis.downloaders.Downloader):
    """Retrieve documents from `theses.fr <https://theses.fr/en/>`__"""

    def __init__(self, url: str) -> None:
        super().__init__(url, name="thesesfr", expected_document_extension="pdf")

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        if re.match(r".*theses.fr.*|\d{4}[a-zA-Z]{3,}\d+", url):
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
        >>> d = Downloader("2014TOU30305")
        >>> d.get_identifier()
        '2014TOU30305'
        """
        if match := re.match(r".*?(\d{4}[a-zA-Z]{3,}\d+)", self.uri):
            return match.group(1)
        else:
            return None

    def get_document_url(self) -> Optional[str]:
        """
        >>> d = Downloader("https://theses.fr/2019REIMS014")
        >>> d.get_document_url()
        'https://theses.fr/api/v1/document/2019REIMS014'
        """

        baseurl = "https://theses.fr/api/v1/document"
        identifier = self.get_identifier()
        return f"{baseurl}/{identifier}"

    def get_bibtex_url(self) -> Optional[str]:
        """
        >>> d = Downloader("https://www.theses.fr/2014TOU30305")
        >>> d.get_bibtex_url()
        'https://www.theses.fr/2014TOU30305.bib'
        """
        url = f"https://www.theses.fr/{self.get_identifier()}.bib"
        self.logger.debug("Using BibTeX URL: '%s'.", url)
        return url
