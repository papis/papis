import re

import papis.downloaders.base


class Downloader(papis.downloaders.Downloader):
    """Retrieve documents from `theses.fr <https://theses.fr/en/>`__

    API Documentation: https://api.gouv.fr/documentation/scanR
    """

    def __init__(self, url: str) -> None:
        super().__init__(url, name="thesesfr", expected_document_extension="pdf")

    @classmethod
    def match(cls, url: str) -> papis.downloaders.Downloader | None:
        # ID format ("nnt" in french). Not specified in the docs, but it's
        # the pattern that all the published theses until now follow.
        # https://documentation.abes.fr/aidetheses/thesesfr/index.html
        if re.match(r"(?:https?://(:?www\.)?theses\.fr/)?(\d{4}[A-Z]{3,5}\d{3,5})",
                    url):
            return Downloader(url)
        else:
            return None

    def get_identifier(self) -> str | None:
        if match := re.search(r"(\d{4}[A-Z]{3,5}\d{3,5})", self.uri):
            return match.group(1)
        else:
            return None

    def get_document_url(self) -> str | None:
        baseurl = "https://theses.fr/api/v1/document"
        identifier = self.get_identifier()
        return f"{baseurl}/{identifier}"

    def get_bibtex_url(self) -> str | None:
        url = f"https://www.theses.fr/{self.get_identifier()}.bib"
        self.logger.debug("Using BibTeX URL: '%s'.", url)
        return url
