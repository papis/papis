import re

import papis.downloaders.base


class Downloader(papis.downloaders.Downloader):
    """Retrieve documents from `AIP Publishing <https://pubs.aip.org>`__"""

    def __init__(self, url: str) -> None:
        super().__init__(
            url, name="scitationaip",
            expected_document_extension="pdf",
            )

    @classmethod
    def match(cls, url: str) -> papis.downloaders.Downloader | None:
        # https://aip.scitation.org/doi/10.1063/1.4873138
        if re.match(r".*(aip|aapt)\.scitation\.org.*", url):
            return Downloader(url)
        else:
            return None

    def get_doi(self) -> str | None:
        mdoi = re.match(r".*/doi/(.*/[^?&%^$]*).*", self.uri)
        if mdoi:
            doi = mdoi.group(1).replace("abs/", "").replace("full/", "")
            return doi
        else:
            return None

    def get_document_url(self) -> str | None:
        # https://aip.scitation.org/doi/pdf/10.1063/1.4873138
        durl = f"https://aip.scitation.org/doi/pdf/{self.get_doi()}"
        self.logger.debug("Using document URL: '%s'.", durl)

        return durl

    def get_bibtex_url(self) -> str | None:
        url = ("https://aip.scitation.org/action/downloadCitation"
               f"?format=bibtex&cookieSet=1&doi={self.get_doi()}")
        self.logger.debug("Using BibTeX URL: '%s'.", url)

        return url
