import re
from typing import Optional, Tuple, Dict

import papis.utils
import papis.downloaders.base


class Downloader(papis.downloaders.Downloader):

    def __init__(self, url: str) -> None:
        super().__init__(url, name="ieee", expected_document_extension="pdf")

    @classmethod
    def match(cls, url: str) -> Optional[papis.downloaders.Downloader]:
        m = re.match(r"^ieee:(.*)", url, re.IGNORECASE)
        if m:
            url = "http://ieeexplore.ieee.org/document/{}".format(m.group(1))
            return Downloader(url)
        if re.match(r".*ieee.org.*", url):
            url = re.sub(r"\.pdf.*$", "", url)
            return Downloader(url)
        else:
            return None

    def get_identifier(self) -> str:
        url = self.uri
        return re.sub(r"^.*ieeexplore\.ieee\.org/document/(.*)\/", r"\1", url)

    def _get_bibtex_url(self) -> Tuple[str, Dict[str, str]]:
        identifier = self.get_identifier()
        bibtex_url = \
            "http://ieeexplore.ieee.org/xpl/downloadCitations?reload=true"
        data = {
            "recordIds": identifier,
            "citations-format": "citation-and-abstract",
            "download-format": "download-bibtex",
            "x": "0",
            "y": "0"
        }
        return bibtex_url, data

    def download_bibtex(self) -> None:
        url, params = self._get_bibtex_url()
        self.logger.debug("bibtex url = '%s'", url)

        session = papis.utils.get_session()
        response = session.get(url, params=params)
        if not response.ok:
            return

        self.bibtex_data = response.content.decode().replace("<br>", "")

    def get_document_url(self) -> Optional[str]:
        identifier = self.get_identifier()
        self.logger.debug("paper id = '%s'", identifier)
        pdf_url = "{}{}{}".format(
            "http://ieeexplore.ieee.org/",
            "stampPDF/getPDF.jsp?tp=&isnumber=&arnumber=",
            identifier)
        self.logger.debug("pdf url = '%s'", pdf_url)
        return pdf_url
