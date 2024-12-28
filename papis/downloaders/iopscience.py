import re
from typing import ClassVar, Optional

import papis.downloaders.base


class Downloader(papis.downloaders.Downloader):
    """Retrieve documents from `IOPscience <https://iopscience.iop.org>`__"""

    DOCUMENT_URL: ClassVar[str] = (
        "https://iopscience.iop.org/article/{doi}/pdf"
        )

    BIBTEX_URL: ClassVar[str] = (
        "https://iopscience.iop.org/export?type=article&doi={doi}"
        "&exportFormat=iopexport_bib"
        "&exportType=abs"
        "&navsubmit=Export%2Babstract")

    def __init__(self, url: str) -> None:
        super().__init__(
            url, name="iopscience",
            expected_document_extension="pdf",
            priority=10,
            )

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        url = url.replace("/pdf", "")
        if re.match(r".*iopscience\.iop\.org.*", url):
            return Downloader(url)
        else:
            return None

    def get_doi(self) -> Optional[str]:
        # NOTE: this is not very robust, but we do not have access to any data
        offset = len("https://iopscience.iop.org/article/")
        return self.uri[offset:]

    def get_document_url(self) -> Optional[str]:
        url = self.ctx.data.get("pdf_url")
        if url is not None:
            return str(url)

        doi = self.get_doi()
        if doi is None:
            return None

        url = self.DOCUMENT_URL.format(doi=doi)
        self.logger.debug("Using document URL: '%s'.", url)

        return url

    def get_bibtex_url(self) -> Optional[str]:
        doi = self.get_doi()
        if doi is None:
            return None

        from urllib.parse import quote_plus

        url = self.BIBTEX_URL.format(doi=quote_plus(doi))
        self.logger.debug("Using BibTeX URL: '%s'.", url)
        return url
