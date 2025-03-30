import re
from typing import Optional

import papis.downloaders.base


class Downloader(papis.downloaders.Downloader):
    """Retrieve documents from `World Scientific <https://www.worldscientific.com>`__"""

    def __init__(self, url: str) -> None:
        super().__init__(
            url, "worldscientific",
            expected_document_extension="pdf",
            cookies={"gdpr": "true"},
            )

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        if re.match(r".*worldscientific.com.*", url):
            return Downloader(url)
        else:
            return None

    def get_doi(self) -> Optional[str]:
        url = self.uri
        self.logger.debug("Parsing DOI from '%s'.", url)
        mdoi = re.match(r".*/doi/(.*/[^?&%^$]*).*", url)
        if mdoi:
            doi = mdoi.group(1).replace("abs/", "").replace("full/", "")
            return doi

        mdoi = re.match(r".*/worldscibooks/(.*/[^?&%^$]*).*", url)
        if mdoi:
            doi = mdoi.group(1).replace("abs/", "").replace("full/", "")
            return doi

        return None

    def get_document_url(self) -> Optional[str]:
        durl = f"https://www.worldscientific.com/doi/pdf/{self.get_doi()}"
        self.logger.debug("Using document URL: '%s'.", durl)
        return durl

    def get_bibtex_url(self) -> Optional[str]:
        url = (
            "https://www.worldscientific.com/action/downloadCitation"
            f"?format=bibtex&cookieSet=1&doi={self.get_doi()}")
        self.logger.debug("Using BibTeX URL: '%s'.", url)

        return url
